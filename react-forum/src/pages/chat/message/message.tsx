import React, {useEffect, useRef, useState} from "react";
import styles from "./message.module.css";
import axios from "axios";
import {API_URL} from "../../../config.ts";
import ImageViewer from "../../../components/imageViewer/imageViewer.tsx";

interface MessageProps {
    id: number;
    message: string;
    isAuthor: boolean;
    profile_image: string;
    files:string[];
}

const Message: React.FC<MessageProps> = (props: MessageProps) => {

    const wrapperRef = useRef<HTMLDivElement>(null);
    const [showContextMenu,setShowContextMenu] = useState(false);
    const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
    const [isModalOpen, setModalOpen] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const handleDeleteButton = () => {
        axios.delete(`${API_URL}/api/chats/${props.id}/delete-message`, {withCredentials:true}).then(() => {
            wrapperRef.current?.remove();
        })
    }

    const handleClickOutside = () => {
        setShowContextMenu(false);
    };

    const handleContextMenu = (event: React.MouseEvent<HTMLDivElement>) => {
        event.preventDefault();

        setMenuPosition({ x: event.pageX, y: event.pageY });
        setShowContextMenu(true);
    };

    useEffect(() => {
        document.body.addEventListener("click", handleClickOutside);
        return () => {
            document.body.removeEventListener("click", handleClickOutside);
        }
    }, [])

    const openImageViewer = (index: number) => {
        setCurrentImageIndex(index);
        setModalOpen(true);
    }

    return (
        <>
            <div onContextMenu={handleContextMenu} ref={wrapperRef} className={styles.message_wrapper}
                 style={props.isAuthor ? {flexDirection: 'row-reverse'} : {}}>
                <img className={styles.image} src={props.profile_image} alt="profile"/>
                <div className={styles.message}>
                    <div className={styles.images_wrapper}>
                        {props.files.map((file, index) => (
                            <img onClick={() => openImageViewer(index)} className={styles.preview_image} key={index} src={file} alt=""/>
                        ))}
                    </div>
                    {props.message}
                </div>
            </div>
            {isModalOpen && (
                <ImageViewer
                    images={props.files}
                    initialIndex={currentImageIndex}
                    onClose={() => setModalOpen(false)}
                />
            )}
            {showContextMenu ? <div
                className={styles.context_menu}
                style={{top: menuPosition.y, left: menuPosition.x}}
            >
                <button onClick={() => handleDeleteButton()}>Действие 1</button>
                <button onClick={() => console.log("Action 2")}>Действие 2</button>
            </div> : null}
        </>
    );
}

export default Message;
