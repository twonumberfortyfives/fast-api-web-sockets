import React from "react";
import {Link} from "react-router-dom";
import styles from "../post.module.css";

type TagProps = {
    tag: string;
};

const Tag: React.FC<TagProps> = ({tag}) => {
    return (
        <Link to={`/tags/${tag}`} className={styles.tag}>
            {tag}
        </Link>
    );
};

export default Tag;