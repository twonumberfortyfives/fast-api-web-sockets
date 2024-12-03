import React from "react";
import styles from "./notFound.module.css";

const NotFound:React.FC = () => {
    return (
        <div className={styles.wrapper}>
            <div className={styles.title}>404</div>
            <div className={styles.text}>Page not found</div>
        </div>
    )
}

export default NotFound