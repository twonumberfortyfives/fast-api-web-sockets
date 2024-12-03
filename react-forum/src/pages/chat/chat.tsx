import Header from "../../components/header/header.tsx";
import styles from "./chat.module.css"
import Message from "./message/message.tsx";
import {Link, useNavigate, useParams} from "react-router-dom";
import backArrow from "../../assets/arrow-back.svg"
import React, {ChangeEvent, useEffect, useRef, useState} from "react";
import {GetApiPaginationGeneric, MessageType, UserType} from "../../types/types.ts";
import axios, {AxiosError} from "axios";
import NotFound from "../../components/notFound/notFound.tsx";
import useAuth from "../../hooks/useAuth.ts";
import {useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import {API_URL, WS_URL} from "../../config.ts";

const Chat = () => {
    const id = Number(useParams().id)

    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [text, setText] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [companion, setCompanion] = useState<UserType | null>(null)
    const [socket, setSocket] = useState<WebSocket | null>(null)
    const [messages, setMessages] = useState<MessageType[]>([])
    const [conversationId, setConversationId] = useState<number | null>(null)
    const [fetching, setFetching] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [isScrolledToBottom, setIsScrolledToBottom] = useState(true);
    const [currentPage, setCurrentPage] = useState(-1);
    const navigate = useNavigate();
    const [files, setFiles] = useState<File[]>([]);
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);

    const userId = useSelector((state: RootState) => state.user.user?.id);

    const isAuth = useAuth()

    useEffect(() => {
        if (isAuth === false) {
            navigate("/login");
        }
    }, [isAuth, navigate]);

    const handleInput = (e: ChangeEvent<HTMLTextAreaElement> | null = null) => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
            window.scrollTo({
                top: document.body.scrollHeight,
            });
        }
        if (e) {
            setText(e.target.value)
        }
    };

    useEffect(() => {
        handleInput();
    }, []);

    useEffect(() => {
        const fetchData = () => {
            if (currentPage === 0) {
                return;
            }

            const pageSize = 20;

            axios.get<GetApiPaginationGeneric<MessageType>>(
                    `${API_URL}/api/chats/${id}?size=${pageSize}&page=${
                        currentPage === -1 ? 1 : currentPage
                    }`,
                    {withCredentials: true}
                )
                .then((res) => {
                    if (currentPage === -1) {
                        setCurrentPage(res.data.pages);
                        return;
                    }

                    setConversationId(res.data.items[0].conversation_id);
                    setMessages((prevMessages) => [...res.data.items, ...prevMessages]);

                    if (scrollRef.current) {
                        const previousScrollHeight = scrollRef.current.scrollHeight;

                        setTimeout(() => {
                            if (scrollRef.current) {
                                const newScrollHeight = scrollRef.current.scrollHeight;
                                scrollRef.current.scrollTop += newScrollHeight - previousScrollHeight;
                            }
                        }, 0);
                    }

                    setIsLoading(false);
                    setFetching(false);

                    if (res.data.items.length < pageSize) {
                        setCurrentPage((prevPage) => prevPage - 1);
                        setFetching(true);
                    }
                })
                .catch((err: AxiosError) => {
                    if (err.response?.status === 400) {
                        setConversationId(-1);
                    }
                    setIsLoading(false);
                    setFetching(false);
                });
        };


        const fetchUser = () => {
            axios
                .get<GetApiPaginationGeneric<UserType>>(`${API_URL}/api/users/${id}`)
                .then((res) => {
                    setCompanion(res.data.items[0]);
                    setIsLoading(true);
                })
                .catch(() => {
                    navigate("/not-found");
                });
        };

        if (fetching) {
            fetchData();
        }

        if (isLoading && !companion) {
            fetchUser();
        }
    }, [companion, currentPage, fetching, id, isLoading, navigate]);



    useEffect(() => {
        if (conversationId && conversationId > 0) {
            const socket = new WebSocket(`${WS_URL}/ws/chats/${conversationId}`)
            setSocket(socket)
            socket.onmessage = (e: MessageEvent<string>) => {

                const newMessage = JSON.parse(e.data)

                newMessage.files = newMessage.files.map((file:string, index:number) => ({ link: file, id: index }));

                setMessages(prevState => [...prevState, newMessage]);
            }
            return () => {
                socket.close()
            }
        }
    }, [conversationId]);

    const handleSend = async () => {
        if (text.trim() === "") {
            return;
        }

        if (socket) {
            const fileDataArray = files.length > 0
                ? await Promise.all(files.map(async file => {
                    const buffer = await convertFileToArrayBuffer(file);
                    return {
                        name: file.name,
                        data: Array.from(new Uint8Array(buffer))
                    };
                }))
                : [];

            socket.send(JSON.stringify({
                content: text.trim(),
                files: fileDataArray
            }));

            setText("");
            setFiles([]);
            setImagePreviews([]);
        } else if (conversationId === -1) {
            axios.post<MessageType>(`${API_URL}/api/chats/${id}/send-message`, { content: text }, { withCredentials: true })
                .then((res) => {
                    setText("")
                    setMessages([res.data]);
                    setConversationId(res.data.conversation_id);
                });
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && e.shiftKey) {
            return;
        }

        if (e.key === "Enter") {
            e.preventDefault();
            handleSend()
        }
    };

    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        const target = e.target as HTMLDivElement;
        const {scrollTop, scrollHeight, clientHeight} = target;
        setIsScrolledToBottom(scrollTop + clientHeight >= scrollHeight);
        if (target.scrollTop < 100 && currentPage > 1 && !fetching) {
            setFetching(true);
            setCurrentPage((prevPage) => prevPage - 1);
        }
    };

    useEffect(() => {
        if (isScrolledToBottom && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isScrolledToBottom]);

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        const newFiles = Array.from(e.dataTransfer.files);
        setFiles((prevFiles) => [...prevFiles, ...newFiles]);

        newFiles.forEach(file => {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreviews((prevPreviews) => [...prevPreviews, reader.result as string]);
            };
            reader.readAsDataURL(file);
        });
    };

    const handleRemoveImage = (index: number) => {
        setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
        setImagePreviews((prevPreviews) => prevPreviews.filter((_, i) => i !== index));
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
    };

    const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
    };

    const convertFileToArrayBuffer = (file: File): Promise<ArrayBuffer> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                if (reader.result) resolve(reader.result as ArrayBuffer);
            };
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    };

    return (
        <>
            <Header/>
            {isLoading ? <div>Loading...</div> :
                companion ? <div className={styles.wrapper}>
                    <div className={styles.header}>
                        <Link className={styles.header__link} to={"/chats"}><img className={styles.header__back_arrow}
                                                                                 src={backArrow} alt="back"/></Link>
                        <Link className={styles.header__link_to_companion} to={`/profile/${id}`}>
                            <img className={styles.header__img} src={companion.profile_picture} alt="profile"/>
                            <div className={styles.title}>{companion.username}</div>
                        </Link>
                    </div>
                    <div className={styles.chat} ref={scrollRef} onScroll={handleScroll}>
                        {messages.map((message, index) => <Message id={message.id} key={index}
                                                                   files={message.files.map(file => file.link)}
                                                                   isAuthor={message.user_id === Number(userId)}
                                                                   message={message.content}
                                                                   profile_image={message.profile_picture}/>)}
                    </div>
                    <div onDragOver={handleDragOver} onDragEnter={handleDragEnter} onDrop={handleDrop}
                         className={styles.footer}>
                        <input style={{display: "none"}} type="file" multiple/>
                        <div className={styles.input_wrapper}>
                            <div className={styles.images_wrapper}>
                                {imagePreviews.map((src, index) => (
                                    <div key={index} className={styles.image_wrapper}>
                                        <img src={src} alt={`file-preview-${index}`}
                                             className={styles.image_preview}/>
                                        <span onClick={() => {
                                            handleRemoveImage(index)
                                        }} className={styles.image_cancel}>X</span>
                                    </div>
                                ))}
                            </div>
                            <textarea style={ imagePreviews.length > 0 ? {borderRadius:"0 0 5px 5px"} : {}} value={text} onChange={handleInput} rows={1} ref={textareaRef}
                                      className={styles.input} onKeyDown={handleKeyDown}/>
                        </div>
                        <div className={styles.button_wrapper}>
                            <button onClick={handleSend} className={styles.button}>Send</button>
                        </div>
                    </div>
                </div> : <NotFound/>}
        </>
    )
}

export default Chat