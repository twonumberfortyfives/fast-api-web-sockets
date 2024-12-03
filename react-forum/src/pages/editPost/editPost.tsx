import React, {useEffect, useState} from "react";
import Header from "../../components/header/header.tsx";
import styles from "./editPost.module.css"
import {useNavigate, useParams} from "react-router-dom";
import {GetApiPaginationGeneric, PostType} from "../../types/types.ts";
import axios, {AxiosError} from "axios";
import NotFound from "../../components/notFound/notFound.tsx";
import {useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import useAuth from "../../hooks/useAuth.ts";
import {API_URL} from "../../config.ts";

const EditPost: React.FC = () => {

    const navigate = useNavigate();

    const {id} = useParams();
    const user = useSelector((state: RootState) => state.user.user);

    const isAuth = useAuth()

    const [post, setPost] = useState<PostType | null>(null)
    const [isLoading, setIsLoading] = useState(true);
    const [topic, setTopic] = useState("");
    const [content, setContent] = useState("");
    const [tags, setTags] = useState("");
    const [error, setError] = useState("");

    const handleTopic = (e:React.ChangeEvent<HTMLTextAreaElement>) =>{
        setTopic(e.target.value);
    }

    const handleContent = (e:React.ChangeEvent<HTMLTextAreaElement>) =>{
        setContent(e.target.value);
    }

    const handleTags = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTags(e.target.value);
    }

    const patchPost = () => {
        let queryString = "";

        if(topic !== post?.topic){
            queryString += `&topic=${encodeURIComponent(topic)}`;
        }

        if(content !== post?.content){
            queryString += `&content=${encodeURIComponent(content)}`;
        }

        if(JSON.stringify(tags.split(" ")) !== JSON.stringify(post?.tags)){
            queryString += `&tags=${encodeURIComponent(tags.split(" ").join(", "))}`;
        }

        if (queryString.length === 0){
            setError("You didn't change anything");
            return;
        }

        axios.patch(`${API_URL}/api/posts/${id}?${queryString}`,{},{withCredentials:true}).then(() => {
            navigate(`/posts/${id}`)
        })
    }

    useEffect(() => {
        const fetchPost = () => {
            axios.get<GetApiPaginationGeneric<PostType>>(`${API_URL}/api/posts/${id}`).then((res) => {
                setIsLoading(false);
                const post = res.data.items[0]
                if(user?.id !== post.user.id){
                    navigate("/login")
                    return;
                }
                setPost(post);
                setTopic(post.topic);
                setContent(post.content);
                setTags(post.tags.join(" "))
            }).catch((err: AxiosError) => {
                console.log(err.status)
                setIsLoading(false);
            })
        }
        if (isAuth === false){
            navigate("/login")
            return
        }
        if (isLoading && isAuth === true) {
            fetchPost()
        }
    }, [id, isAuth, isLoading, navigate, user?.id])

    return (
        <>
            <Header/>
            {isLoading ? <div>Loading...</div> : post ? <div className={styles.content}>
                <div className={styles.title}>Edit Post</div>
                {error ? <div className={styles.error}>{error}</div> : ""}
                <div className={styles.label}>Topic:</div>
                <textarea value={topic} onChange={handleTopic} className={styles.textarea}/>
                <div className={styles.label}>Description:</div>
                <textarea value={content} onChange={handleContent}
                          className={`${styles.textarea} ${styles.description}`}/>
                <div className={styles.label}>Tags:</div>
                <input value={tags} onChange={handleTags} className={styles.tags}></input>
                <div className={styles.buttons}>
                    <button onClick={()=>{navigate(-1)}} className={styles.button}>Back</button>
                    <button onClick={patchPost} className={styles.button}>Confirm</button>
                </div>
            </div> : <NotFound/>}
        </>
    )
}

export default EditPost;