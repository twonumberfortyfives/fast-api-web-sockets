import styles from "./user.module.css";
import React from "react";
import {Link} from "react-router-dom";

interface PropsType {
    id: number;
    username: string;
    profile_picture: string;
}

const User: React.FC<PropsType> = ({id,username,profile_picture}:PropsType) => {
    return (
        <Link to={`/profile/${id}`} className={styles.wrapper}>
            <img className={styles.img} src={profile_picture} alt="avatar"/>
            <div className={styles.text}>{username}</div>
        </Link>
    )
}

export default User