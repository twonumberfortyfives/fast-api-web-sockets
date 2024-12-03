import React, {useEffect, useState} from 'react';
import Header from "../../components/header/header.tsx";
import styles from "./register.module.css"
import {Link, useNavigate} from "react-router-dom";
import useAuth from "../../hooks/useAuth.ts";
import axios from "axios";
import {API_URL} from "../../config.ts";

const Register: React.FC = () => {

    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordAgain, setPasswordAgain] = useState("");

    const [error, setError] = useState("");

    const navigate = useNavigate();
    const isAuth = useAuth()

    const numberRegex: RegExp = /\d/;
    const uppercaseRegex: RegExp = /[A-Z]/;

    useEffect(() => {
        if(isAuth){
            navigate("/profile");
        }
    })

    const handleUsername = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setUsername(e.target.value);
    }

    const handleEmail = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setEmail(e.target.value);
    }

    const handlePassword = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setPassword(e.target.value);
    }

    const handlePasswordAgain = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setPasswordAgain(e.target.value);
    }

    const handleButton = (): void => {
        setError("");
        if(username === "" || email === "" || password === "" || passwordAgain === "" ){
            setError("Please fill all fields");
            return;
        }
        if(username.length < 3 || username.length > 20){
            setError("Username must be between 3 and 20 characters");
            return;
        }
        if(!email.includes("@") && !email.includes(".")){
            setError("Please enter a valid email");
            return;
        }
        if(password.length < 8 || password.length > 20){
            setError("Password must be between 8 and 20 characters");
            return;
        }
        if(!numberRegex.test(password)){
            setError("Password must contain a number");
            return;
        }
        if(!uppercaseRegex.test(password)){
            setError("Password must contain uppercase");
            return;
        }
        if (password !== passwordAgain){
            setError("Passwords must to be same");
            return;
        }

        axios.post(`${API_URL}/api/register`, {username, email, password}, {withCredentials:true}).then((res) => {
            console.log(res)
            navigate("/login", {replace: true});
        }).catch((err) => {
            console.log(err)
        })
    }

    return (
        <>
            <Header/>
            <div className={styles.content}>
                <div className={styles.title}>Register</div>
                {error ? <div className={styles.error}>{error}</div> : null}
                <input value={username} onChange={handleUsername} placeholder="User name" className={styles.input} type="text"/>
                <input value={email} onChange={handleEmail} placeholder="Email" className={styles.input} type="email"/>
                <input value={password} onChange={handlePassword} placeholder="Password" className={styles.input}
                       type="password"/>
                <input value={passwordAgain} onChange={handlePasswordAgain} placeholder="Password again"
                       className={styles.input} type="password"/>
                <button onClick={handleButton} className={styles.button}>Sing Up</button>
                <div className={styles.sing_up}>Do you have an account? <Link className={styles.link} to={"/login"}>Sing
                    In</Link></div>
            </div>
        </>
    );
};

export default Register;