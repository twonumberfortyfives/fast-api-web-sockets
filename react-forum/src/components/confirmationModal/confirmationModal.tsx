import React from 'react';
import styles from './confirmationModal.module.css';

interface ConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    text: string;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({ isOpen, onClose, onConfirm, text }) => {
    if (!isOpen) return null;

    return (
        <div className={styles.wrapper}>
            <div className={styles.content}>
                <div className={styles.text}>{text}</div>
                <div className={styles.buttons}>
                    <button className={styles.cancel} onClick={onClose}>Cancel</button>
                    <button className={styles.confirm} onClick={onConfirm}>Confirm</button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;
