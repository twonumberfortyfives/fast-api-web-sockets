import React, {useEffect, useRef, useState} from "react";
import styles from "./createPost.module.css";
import Header from "../../components/header/header.tsx";
import {useLocation, useNavigate} from "react-router-dom";
import useAuth from "../../hooks/useAuth.ts";
import paperIcon from "../../assets/paper-icon.svg"
import axios from "axios";
import {API_URL} from "../../config.ts";

const CreatePost: React.FC = () => {
    const [topic, setTopic] = useState("");
    const [content, setContent] = useState("");
    const [tags, setTags] = useState("");
    const [error, setError] = useState("");
    const [onDrag, setOnDrag] = useState(false);
    const [files, setFiles] = useState<File[]>([]);
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const location = useLocation();
    const navigate = useNavigate();
    const isAuthenticated = useAuth();

    useEffect(() => {
        if (isAuthenticated === false) {
            navigate("/login");
        }
        if (location.state && location.state.topic) {
            setTopic(location.state.topic);
        }
    }, [isAuthenticated, location.state, navigate]);

    const handleTopic = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
        setTopic(e.target.value);
    };

    const handleContent = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
        setContent(e.target.value);
    };

    const handleTags = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setTags(e.target.value);
    };

    const handleCreate = (): void => {
        const formData = new FormData();

        if (topic.length < 3 || topic.length > 200) {
            setError("Topic must be between 3 and 200 characters.");
            return;
        }

        if (content.length < 10 || content.length > 800) {
            setError("Content must be between 10 and 800 characters.");
            return;
        }

        if(files.length > 0){
            files.forEach((file) => {
                formData.append('files', file);
            });
        }
        else {
            formData.append('files', "");
        }
        const queryParams = `?topic=${encodeURIComponent(topic.trim())}&content=${encodeURIComponent(content.trim())}${tags ? `&tags=${encodeURIComponent(tags.split(" ").join(", "))}` : ""}`;

        axios.post(`${API_URL}/api/posts${queryParams}`, formData, {
            withCredentials: true,
            headers: {
                "Content-Type": "multipart/form-data",
            }
        })
            .then((res) => {
                navigate(`/posts/${res.data.id}`);
            })
            .catch((err) => {
                console.log(err.response);
            });
    };


    const handleDragStart = (e: React.DragEvent<HTMLTextAreaElement | HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setOnDrag(true);
    };

    const handleDragLeave = (e: React.DragEvent<HTMLTextAreaElement | HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setOnDrag(false);
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setOnDrag(false);
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

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg'];
        const newFiles = Array.from(event.target.files || []).filter(file => allowedTypes.includes(file.type));

        if (newFiles.length === 0) {
            setError("Only PNG, JPG, and JPEG formats are allowed.");
            return;
        }

        setFiles((prevFiles) => [...prevFiles, ...newFiles]);

        newFiles.forEach(file => {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreviews((prevPreviews) => [...prevPreviews, reader.result as string]);
            };
            reader.readAsDataURL(file);
        });
    };


    const handlePaperClip = () => {
        fileInputRef.current?.click()
    }

    return (
        <>
            <Header/>
            <div className={styles.content}>
                <div className={styles.title}>Create Post</div>
                {error ? <div className={styles.error}>{error}</div> : null}
                <div className={styles.label}>Topic:</div>
                <textarea value={topic} onChange={handleTopic} className={styles.textarea}/>

                <div className={styles.images_wrapper}>
                    <div>Images:</div>
                    <button onClick={handlePaperClip}>
                        <img className={styles.images_wrapper__img} src={paperIcon} alt=""/>
                    </button>
                    <input onChange={handleFileChange} ref={fileInputRef} style={{display: "none"}} type="file"
                           accept="image/png, image/jpg, image/jpeg" multiple/>
                </div>
                <div
                    className={styles.files_wrapper}
                    onDragStart={handleDragStart}
                    onDragLeave={handleDragLeave}
                    onDragOver={handleDragStart}
                >
                    <div className={styles.files}>
                        {imagePreviews.length === 0 ? (
                            <div className={styles.empty}>Empty</div>
                        ) : (
                            imagePreviews.map((src, index) => (
                                <div key={index} className={styles.image_wrapper}>
                                    <img src={src} alt={`file-preview-${index}`}
                                         className={styles.image_preview}/>
                                    <span onClick={()=> {handleRemoveImage(index)}} className={styles.image_cancel}>X</span>
                                </div>
                            ))
                        )}
                    </div>
                    <div
                        style={onDrag ? {} : {display: "none"}}
                        className={styles.textarea__absolute_block}
                        onDragStart={handleDragStart}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragStart}
                        onDrop={handleDrop}
                    >
                        Drop files for uploading
                    </div>
                </div>

                <div className={`${styles.label} ${styles.decr_label}`}>Description:</div>
                <textarea
                    value={content}
                    onChange={handleContent}
                    className={`${styles.textarea} ${styles.description}`}
                />

                <div className={styles.label}>Tags:</div>
                <input value={tags} onChange={handleTags} className={styles.tags}></input>

                <div className={styles.button_wrapper}>
                    <button onClick={handleCreate} className={styles.button}>Create</button>
                </div>
            </div>
        </>
    );
};

export default CreatePost;
