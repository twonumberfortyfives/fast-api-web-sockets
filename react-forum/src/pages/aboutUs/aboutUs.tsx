import Header from "../../components/header/header.tsx";
import styles from "./aboutUs.module.css"
import React from "react";

const AboutUs:React.FC = () =>{
    return (
        <>
            <Header/>

            <div className={styles.wrapper}>
                <div className={styles.about_us}>
                    <div className={styles.title}>About Our Project</div>
                    <div>This forum is a pet project aimed at creating a functional and stylish community platform.</div>
                </div>

                <div className={styles.team}>
                    <div className={styles.title}>Our Team</div>
                    <div className={styles.team__item}>
                        <div><strong>Nazar:</strong> Front-end Developer</div>
                        <a href="https://github.com/guziiuchyk">GitHub</a>
                        <a href="https://drive.google.com/file/d/1Ze-mHMHQSOcu2AGutkv_g-jH7EB4RSRg/view?usp=sharing">CV</a>
                    </div>
                    <div className={styles.team__item}>
                        <div><strong>Maksim:</strong> Back-end Developer</div>
                        <a href="https://github.com/twonumberfortyfives">GitHub</a>
                        <a href="https://drive.google.com/file/d/1HfoJr5mGtFPtDffe-84r4uAXBNaypc9g/view?usp=sharing">CV</a>
                    </div>
                </div>

                <div className={styles.project_info}>
                    <div className={styles.title}>Project Information</div>
                    <div className={styles.project_info__text}>You can check out the source code on GitHub:</div>
                    <div><a href="https://github.com/guziiuchyk/react-forum" target="_blank">Frontend Repository</a></div>
                    <div><a href="https://github.com/twonumberfortyfives/fast-api-web-sockets" target="_blank">Backend Repository</a></div>
                </div>
            </div>
        </>
    )
}

export default AboutUs;