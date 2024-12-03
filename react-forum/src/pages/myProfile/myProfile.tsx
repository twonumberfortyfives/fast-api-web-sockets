import React, {useEffect} from 'react';
import Header from "../../components/header/header.tsx";
import styles from "./myProfile.module.css";
import {useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import useAuth from "../../hooks/useAuth.ts";
import {useNavigate} from "react-router-dom";
import {UserType} from "../../types/types.ts";
import PostsPagination from "../../components/postsPagination/postsPagination.tsx";
import {API_URL} from "../../config.ts";

const MyProfile: React.FC = () => {

    const isAuthenticated = useAuth();
    const navigate = useNavigate();

    const user = useSelector((state: RootState) => state.user.user as UserType | null);

    useEffect(() => {
        if (isAuthenticated === false) {
            navigate("/login");
        }
    }, [isAuthenticated, navigate]);

    return (
        <>
            <Header/>
            {user ? <div className={styles.content}>
                    <div className={styles.profile_wrapper}>
                        <img width={200} height={200} src={user.profile_picture} alt="MyProfile"
                             className={styles.profile__img}/>
                        <div className={styles.profile_info}>
                            <div className={styles.profile__name}>{user.username}</div>
                            <div className={styles.profile__desc}>{user.bio}</div>
                        </div>
                    </div>

                    <div className={styles.posts_wrapper}>
                        <PostsPagination link={`${API_URL}/api/users/${user.id}/posts/`}/>
                    </div>
                </div>
                : <div>Loading...</div>}
        </>
    );
};

export default MyProfile;
