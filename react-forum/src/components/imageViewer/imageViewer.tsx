import React, {useEffect, useRef, useState} from "react";
import styles from "./imageViewer.module.css";

interface ImageViewerProps {
    images: string[];
    initialIndex: number;
    onClose: () => void;
}

const ImageViewer: React.FC<ImageViewerProps> = ({images, initialIndex, onClose}) => {
    const [currentIndex, setCurrentIndex] = useState(initialIndex);
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        document.body.style.overflow = "hidden";

        return () => {
            document.body.style.overflow = "auto";
        };
    }, []);

    const prevImage = () => {
        setCurrentIndex((prevIndex) => (prevIndex === 0 ? images.length - 1 : prevIndex - 1));
    };

    const nextImage = () => {
        setCurrentIndex((prevIndex) => (prevIndex === images.length - 1 ? 0 : prevIndex + 1));
    };

    const handleClose = (e:React.MouseEvent<HTMLDivElement>) => {
        if(e.target == modalRef.current){
            onClose();
        }
    }

    return (
        <div ref={modalRef} onClick={handleClose} className={styles.modal}>
            <div className={styles.modal_content}>
                <span className={styles.close} onClick={onClose}>
                    &times;
                </span>
                <img src={images[currentIndex]} alt={`image-${currentIndex}`} className={styles.image}/>
            </div>
            <div className={styles.controls}>
                <button onClick={prevImage} className={styles.arrow}>&larr;</button>
                <button onClick={nextImage} className={styles.arrow}>&rarr;</button>
            </div>
        </div>
    );
};

export default ImageViewer;
