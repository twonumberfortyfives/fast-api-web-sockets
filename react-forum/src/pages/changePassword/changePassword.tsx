import styles from "./changePassword.module.css"
import Header from "../../components/header/header.tsx";
import React, {useEffect, useState} from "react";
import axios, {AxiosError} from "axios";
import {useNavigate} from "react-router-dom";
import useAuth from "../../hooks/useAuth.ts";
import {API_URL} from "../../config.ts";

const ChangePassword:React.FC = () => {
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();
    const isAuth = useAuth();
    const numberRegex: RegExp = /\d/;
    const uppercaseRegex: RegExp = /[A-Z]/;
    
    useEffect(() => {
        if(isAuth === false){
            navigate("/login");
        }
    }, [isAuth, navigate])
    
    const handleOldPassword = (e: React.ChangeEvent<HTMLInputElement>) => {
        setOldPassword(e.target.value);
    }

    const handleNewPassword = (e: React.ChangeEvent<HTMLInputElement>) => {
        setNewPassword(e.target.value);
    }

    const handleSubmit = () => {
        setError("")
        if(oldPassword === "" && newPassword === ""){
            setError("Please fill all fields");
            return;
        }
        if(newPassword.length < 8 || newPassword.length > 20){
            setError("New password must be between 8 and 20 characters");
            return;
        }
        if(!numberRegex.test(newPassword)){
            setError("New password must contain a number");
            return;
        }
        if(!uppercaseRegex.test(newPassword)){
            setError("New password must contain uppercase");
            return;
        }
        axios.patch(`${API_URL}/api/my-profile/change-password`, {"old_password":oldPassword, "new_password": newPassword}, {withCredentials:true}).then(() => {
            navigate("/profile")
        }).catch((err: AxiosError) => {
            if(err.response?.status === 401){
                setError("Passwords do not match");
            }
        })
    }
    return (
        <>
            <Header/>
            <div className={styles.wrapper}>
                <div className={styles.title}>Change password</div>
                {error ? <div className={styles.error}>{error}</div> : null}
                <div className={styles.label}>Old password:</div>
                <input autoComplete="new-password" className={styles.input} value={oldPassword} onChange={handleOldPassword} type="text"/>
                <div className={styles.label}>New password:</div>
                <input autoComplete="new-password" className={styles.input} value={newPassword} onChange={handleNewPassword} type="password"/>
                <button onClick={handleSubmit} className={styles.button}>Confirm</button>
            </div>
        </>
    )
}

export default ChangePassword;