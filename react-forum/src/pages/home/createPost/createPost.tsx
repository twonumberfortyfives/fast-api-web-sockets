import React, {useState} from "react";
import styles from "./createPost.module.css"
import {useNavigate} from "react-router-dom";
import {useSelector} from "react-redux";
import {RootState} from "../../../redux/store.ts";

const Home: React.FC = () => {

    const [text, setText] = useState("");

     const profile_picture = useSelector((state:RootState) => state.user.user?.profile_picture);

    const navigate = useNavigate();

    const handleText = (e: React.ChangeEvent<HTMLInputElement>) => {
        setText(e.target.value);
    }

    const handleButton = ():void => {
        navigate("/create-post", {state:{topic:text}});
    }

    return (
        <>
            <div className={styles.wrapper}>
                {profile_picture ? <img className={styles.img} src={profile_picture} alt=""/> : null}
                <input value={text} onChange={handleText} placeholder="Let’s share what going on your mind..." className={styles.text}/>
                <button onClick={handleButton} className={styles.button}>Create Post</button>
            </div>
        </>
    );
};

export default Home;