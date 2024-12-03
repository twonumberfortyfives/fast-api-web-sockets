import React, {ChangeEvent, useEffect, useRef, useState} from "react";
import Comment from "./comment/comment.tsx";
import styles from "../postPage.module.css";
import useAuth from "../../../hooks/useAuth.ts";
import {CommentType, GetApiPaginationGeneric, PostType} from "../../../types/types.ts";
import {useSelector} from "react-redux";
import {RootState} from "../../../redux/store.ts";
import axios from "axios";
import {API_URL, WS_URL} from "../../../config.ts";

type PropsType = {
    id: number;
    setPost: React.Dispatch<React.SetStateAction<PostType | null>>;
    authorId: number;
}

const Comments: React.FC<PropsType> = (props: PropsType) => {

    const [text, setText] = useState("");
    const isAuth = useAuth();
    const userId = useSelector((state: RootState) => state.user.user?.id);
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [comments, setComments] = useState<CommentType[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [isScrolledToBottom, setIsScrolledToBottom] = useState(true);
    const [currentPage, setCurrentPage] = useState(-1);
    const [fetching, setFetching] = useState(true);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        const fetchComments = () => {
            axios.get<GetApiPaginationGeneric<CommentType>>(`${API_URL}/api/posts/${props.id}/all-comments?size=10&page=${currentPage === -1 ? 1 : currentPage}`).then(res => {
                if (currentPage === -1) {
                    setCurrentPage(res.data.pages);
                    return;
                }

                if (scrollRef.current) {
                    const previousScrollHeight = scrollRef.current.scrollHeight;

                    setComments((prevComments) => [...res.data.items, ...prevComments]);

                    setTimeout(() => {
                        if (scrollRef.current) {
                            const newScrollHeight = scrollRef.current.scrollHeight;
                            const scrollOffset = newScrollHeight - previousScrollHeight;
                            scrollRef.current.scrollTop += scrollOffset;
                        }
                    }, 0);
                }
                setFetching(false);
            })
        }

        if (fetching) {
            fetchComments();
        }
    }, [props.id, currentPage, fetching]);

    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        const target = e.target as HTMLDivElement;
        if (target.scrollTop < 100 && currentPage > 1 && !fetching) {
            setFetching(true);
            setCurrentPage((prevPage) => prevPage - 1);
        }
    };

    useEffect(() => {
        const socket = new WebSocket(`${WS_URL}/ws/posts/${props.id}`);
        socket.onmessage = (e: MessageEvent<string>) => {
            const comment = JSON.parse(e.data) as CommentType;
            setComments((prevComments) => [...prevComments, comment]);
            props.setPost(prevState => {
                if (prevState) {
                    return {
                        ...prevState,
                        comments_count: prevState.comments_count + 1
                    }
                }
                return prevState;
            })
        };
        setSocket(socket);

        return () => {
            socket.close();
        };
    }, []);

    useEffect(() => {
        const currentRef = scrollRef.current;
        if (currentRef) {
            const handleScroll = () => {
                const {scrollTop, scrollHeight, clientHeight} = currentRef;
                setIsScrolledToBottom(scrollTop + clientHeight >= scrollHeight);
            };

            currentRef.addEventListener('scroll', handleScroll);
            return () => currentRef.removeEventListener('scroll', handleScroll);
        }
    }, []);

    useEffect(() => {
        if (isScrolledToBottom && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [comments, isScrolledToBottom]);

    const handleSend = () => {
        if (socket && isAuth && text) {
            socket.send(JSON.stringify(text));
            setText("");
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleInput = (e: ChangeEvent<HTMLTextAreaElement> | null = null) => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
        if (e) {
            setText(e.target.value);
        }
    };

    useEffect(() => {
        handleInput();
    }, []);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && e.shiftKey) {
            return;
        }

        if (e.key === "Enter") {
            e.preventDefault();
            handleSend()
        }
    };

    return (
        <div onScroll={handleScroll} ref={scrollRef} className={styles.chat_container}>
            {comments.map((comment, index) => (
                <Comment key={index} {...comment} isAuthor={props.authorId === userId}/>
            ))}
            {isAuth ? <div className={styles.send_message}>
                <textarea
                    value={text}
                    ref={textareaRef}
                    onChange={handleInput}
                    className={styles.send_message__input}
                    placeholder="Write a comment..."
                    rows={1}
                    onKeyDown={handleKeyDown}
                />
                <div className={styles.button_wrapper}>
                    <button onClick={handleSend} className={styles.send_message__button}>Send</button>
                </div>
            </div> : null}
        </div>
    )
}

export default Comments;