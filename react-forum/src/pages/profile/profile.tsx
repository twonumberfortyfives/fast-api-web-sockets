import styles from "./profile.module.css";
import React, {useEffect, useState} from "react";
import Header from "../../components/header/header.tsx";
import {GetApiPaginationGeneric, UserType} from "../../types/types.ts";
import axios from "axios";
import {Link, useNavigate, useParams} from "react-router-dom";
import NotFound from "../../components/notFound/notFound.tsx";
import {useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import PostsPagination from "../../components/postsPagination/postsPagination.tsx";
import {API_URL} from "../../config.ts";

const Profile: React.FC = () => {

    const navigate = useNavigate();

    const [isLoading, setIsLoading] = useState(true);
    const [user, setUser] = useState<UserType | null>(null);

    const {id} = useParams();

    const userId = useSelector((state: RootState) => state.user.user?.id);

    useEffect(() => {
        const fetchUser = () => {
            axios.get<GetApiPaginationGeneric<UserType>>(`${API_URL}/api/users/${id}`).then((res) => {
                setUser(res.data.items[0]);
                setIsLoading(false);
            })
        }

        fetchUser()
    }, [id]);

    useEffect(() => {
        if (Number(id) === userId) {
            navigate("/profile", {replace: true});
        }
    })

    return (
        <>
            <Header/>
            {isLoading ? <div>Loading...</div> : user ?
                <>
                    <div className={styles.profile_wrapper}>
                        <img width={200} height={200} src={user.profile_picture} alt="profile"
                             className={styles.profile__img}/>
                        <div className={styles.profile_info}>
                            <div className={styles.profile__name}>{user.username}</div>
                            <div className={styles.profile__desc}>{user.bio}</div>
                        </div>
                        <div className={styles.profile__nav}>
                            <Link to={`/chats/${id}`} className={styles.button}>Send Message</Link>
                        </div>
                    </div>
                    <div className={styles.posts_wrapper}>
                        {isLoading ? <div>Loading...</div> :
                            <PostsPagination link={`${API_URL}/api/users/${id}/posts/`}/>}
                    </div>
                </>
                : <NotFound/>}
        </>
    )
}

export default Profile;