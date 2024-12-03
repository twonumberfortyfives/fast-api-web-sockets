import {useNavigate} from "react-router-dom";
import React from "react";
import styles from "../chats.module.css";

interface ChatProps {
    profile_image: string;
    username: string;
    last_message: string;
    user_id: number;
}

const Chat = (props: ChatProps) => {

    const navigate = useNavigate();

    const navigateToProfile = (e: React.MouseEvent<HTMLDivElement | HTMLImageElement>) => {
        e.stopPropagation();
        navigate(`/profile/${props.user_id}`)
    }

    return (
        <div className={styles.chat} onClick={() => {navigate(`/chats/${props.user_id}`)}}>
            <img onClick={navigateToProfile} className={styles.chat__image} src={props.profile_image} alt="Image"/>
            <div className={styles.user_and_message}>
                <div onClick={navigateToProfile} className={styles.username}>{props.username}</div>
                <div className={styles.last_message}>{props.last_message}</div>
            </div>
        </div>
    )
}

export default Chat
