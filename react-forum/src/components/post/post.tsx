import React, {useRef, useState} from "react";
import styles from "./post.module.css";
import {Link, useNavigate} from "react-router-dom";
import likeImage from "../../assets/like.svg"
import likeActiveImage from "../../assets/like-active.svg"

import removeImage from "../../assets/remove.svg"
import editImage from "../../assets/edit.svg"
import useTimeAgo from "../../hooks/useTimeAgo.ts";
import {useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import axios from "axios";
import Tag from "./tag/tag.tsx";
import ConfirmationModal from "../confirmationModal/confirmationModal.tsx";
import {API_URL} from "../../config.ts";

interface PostProps {
    "id": number,
    "topic": string,
    "created_at": string,
    tags: string[],
    isLiked: boolean,
    info: { comments: number, likes: number },
    author: {
        username: string,
        id: number,
        profile_picture: string
    }
}

const Post: React.FC<PostProps> = (props) => {

    const {topic, tags, info, id, created_at, author} = props;

    const navigate = useNavigate();

    const formatedDate = useTimeAgo(created_at);
    const {isAuthenticated,user} = useSelector((state: RootState) => state.user);
    const isAuthor = author.id === user?.id;
    const wrapperRef = useRef<HTMLDivElement | null>(null)
    const [isModalOpen, setModalOpen] = useState(false);
    const [isLiked, setIsLiked] = useState<boolean>(props.isLiked);

    const deletePost = (id:number) => {
        axios.delete(`${API_URL}/api/posts/${id}`, {withCredentials:true}).then(()=> {
            if(wrapperRef.current) {
                wrapperRef.current.remove();
            }
        }).catch((err)=>{
            console.log(err)
        })
    }

    const handleLikeButton = (id:number) => {
        if(!isAuthenticated) return;
        if(isLiked){
            axios.delete(`${API_URL}/api/posts/${id}/like/`, {withCredentials:true}).then(()=> {
                info.likes -= 1
                setIsLiked(false)
            })
        } else {
            axios.post(`${API_URL}/api/posts/${id}/like/`, {}, {withCredentials:true}).then(()=> {
                info.likes += 1
                setIsLiked(true)
            })
        }
    }

    return (
        <div ref={wrapperRef} className={styles.wrapper}>
            <Link to={`/posts/${id}`} className={styles.title}>{topic.trim()}</Link>
            <div className={styles.buttons_wrapper}>
                {isAuthor ? <>
                    <button onClick={()=>{navigate(`/edit-post/${id}`)}}>
                        <div className={styles.button}>
                            <img className={styles.button__img} src={editImage} alt="like"/>
                        </div>
                    </button>
                    <button onClick={()=>{setModalOpen(true)}}>
                        <div className={styles.button}>
                            <img className={styles.button__img} src={removeImage} alt="like"/>
                        </div>
                    </button>
                </> : ""}
                <button onClick={()=> {handleLikeButton(id)}}>
                    <div className={styles.button}><img className={styles.button__img}
                                                        src={isLiked ? likeActiveImage : likeImage} alt="like"/></div>
                </button>
            </div>
            <div className={styles.tags}>
                {tags?.map(tag => (<Tag key={tag} tag={tag}/>))}
            </div>
            <div className={styles.author}>
                <img className={styles.author__img} src={author.profile_picture} alt="author"/>
                <div className={styles.author_info}>
                    <Link to={isAuthor ? "/profile" : `/profile/${author.id}`} className={styles.author__name}>{author.username}</Link>
                    <span className={styles.info__date}>{formatedDate}</span>
                </div>
            </div>
            <div className={styles.info}>
                <span className={styles.info__element}>{info.likes} likes</span>
                <span className={styles.info__element}>{info.comments} comments</span>
            </div>
            <ConfirmationModal
                text={"Are you sure you want to delete this post?"}
                isOpen={isModalOpen}
                onClose={() => setModalOpen(false)}
                onConfirm={()=>{deletePost(id)}}
            />
        </div>
    );
};

export default Post;