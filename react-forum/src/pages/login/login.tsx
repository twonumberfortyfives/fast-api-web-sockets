import React, {useEffect, useState} from 'react';
import Header from "../../components/header/header.tsx";
import styles from "./login.module.css"
import {Link, useNavigate} from "react-router-dom";
import axios from "axios";
import useAuth from "../../hooks/useAuth.ts";
import {useDispatch} from "react-redux";
import {login} from "../../redux/slices/userSlice.ts";
import {API_URL} from "../../config.ts";

const Login: React.FC = () => {

    const navigate = useNavigate();
    const dispatch = useDispatch();
    const isAuth = useAuth()

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        if (isAuth) {
            navigate("/profile");
        }
    })

    const handleLogin = (): void => {

        if (!email || !password) {
            setError("Wrong email or password");
            return;
        }

        axios.post(`${API_URL}/api/login`, {email, password}, {
            withCredentials: true
        }).then(() => {
            axios.get(`${API_URL}/api/my-profile`, {withCredentials:true}).then((res) => {
                dispatch(login(res.data));
                navigate("/profile");
            })
        }).catch(() => {
            setError("Wrong email or password");
        })

    }

    const onChangeLogin = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setEmail(e.target.value);
    }
    const onChangePassword = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setPassword(e.target.value);
    }
    return (
        <>
            <Header/>
            <div className={styles.content}>
                <div className={styles.title}>Login</div>
                <span className={styles.error}>{error}</span>
                <input onChange={onChangeLogin} value={email} placeholder="Email" className={styles.input} type="text"/>
                <input onChange={onChangePassword} value={password} placeholder="Password" className={styles.input}
                       type="password"/>
                <button onClick={handleLogin} className={styles.button}>Sing In</button>
                <div className={styles.sing_up}>Dont have an account? <Link className={styles.link} to={"/register"}>Sing
                    Up</Link></div>
            </div>
        </>
    );
};

export default Login;