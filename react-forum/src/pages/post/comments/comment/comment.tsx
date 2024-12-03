import React from "react";
import {CommentType} from "../../../../types/types.ts";
import styles from "./comment.module.css"
import useTimeAgo from "../../../../hooks/useTimeAgo.ts";

interface CommentProps extends CommentType {
    isAuthor: boolean;
}

const Comment: React.FC<CommentProps> = (props) => {
    const date = useTimeAgo(props.created_at);
    return (
        <div className={styles.comment}>
            <img src={props.profile_picture} alt="Avatar" className={styles.avatar}/>
            <div className={styles.content}>
                <div className={styles.title}>
                    <div className={styles.username}>{props.username}</div>
                    <div className={styles.timestamp}>{date}</div>
                </div>
                <div>{props.content}</div>
            </div>
        </div>)
}

export default Comment