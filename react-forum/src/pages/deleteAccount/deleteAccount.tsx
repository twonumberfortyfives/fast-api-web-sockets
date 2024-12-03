import styles from "./deleteAccount.module.css"
import Header from "../../components/header/header.tsx";
import React, {useEffect, useState} from "react";
import axios from "axios";
import useAuth from "../../hooks/useAuth.ts";
import {useNavigate} from "react-router-dom";
import ConfirmationModal from "../../components/confirmationModal/confirmationModal.tsx";
import {API_URL} from "../../config.ts";

const DeleteAccount:React.FC = () => {

    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isModalOpen, setModalOpen] = useState(false);
    const isAuth = useAuth();
    const navigate = useNavigate();
    useEffect(() => {
        if(isAuth === false){
            navigate("/login");
        }
    }, [isAuth, navigate]);

    const handlePassword = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPassword(e.target.value);
    }

    const handleDelete = () => {
        axios.delete(`${API_URL}/api/my-profile`, {data:{password}, withCredentials:true}).then(() => {
            navigate("/login");
        }).catch(()=>{
            setError("Wrong password.");
        })
        setModalOpen(false);
    }

    return (
        <>
            <Header/>
            <div className={styles.wrapper}>
                <div className={styles.title}>DELETE ACCOUNT</div>
                {error ? <div className={styles.error}>{error}</div>: null}
                <div className={styles.label}>Password:</div>
                <input autoComplete="new-password" className={styles.input} value={password}
                       onChange={handlePassword} type="password"/>
                <button onClick={()=> {setModalOpen(true)}} className={styles.button}>Confirm</button>
            </div>
            <ConfirmationModal
                text="Are you sure you want to delete you account?"
                isOpen={isModalOpen}
                onClose={() => setModalOpen(false)}
                onConfirm={handleDelete}
            />
        </>
    )
}

export default DeleteAccount;