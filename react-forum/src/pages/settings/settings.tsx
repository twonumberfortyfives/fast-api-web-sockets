import styles from "./settings.module.css"
import Header from "../../components/header/header.tsx";
import React, {useEffect} from "react";
import useAuth from "../../hooks/useAuth.ts";
import {Link, useNavigate} from "react-router-dom";

const Settings: React.FC = () => {

    const isAuth = useAuth()
    const navigate = useNavigate()

    useEffect(() => {
        if(isAuth === false){
            navigate("/login");
        }
    }, [isAuth, navigate])

    return (
        <>
            <Header/>
            <div className={styles.wrapper}>
                <div className={styles.title}>settings</div>
                <Link to={"/settings/change-password"}><button className={styles.change_password}>Change password</button></Link>
                <Link to={"/settings/delete-account"}><button className={styles.delete_account}>Delete account</button></Link>
            </div>
        </>
    )
}

export default Settings;