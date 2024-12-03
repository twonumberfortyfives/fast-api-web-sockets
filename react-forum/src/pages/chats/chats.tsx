import styles from "./chats.module.css"
import Header from "../../components/header/header.tsx";
import React, {useEffect, useState} from "react";
import Chat from "./chat/chat.tsx";
import {ChatType, GetApiPaginationGeneric} from "../../types/types.ts";
import axios from "axios";
import useAuth from "../../hooks/useAuth.ts";
import {useNavigate} from "react-router-dom";
import {API_URL} from "../../config.ts";

const Chats: React.FC = () => {

    const [isLoading, setIsLoading] = useState(true);
    const [chats, setChats] = useState<ChatType[]>([]);
    const isAuth = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if(isAuth === false){
            navigate("/login");
        }
    }, [isAuth, navigate]);

    useEffect(() => {
        const fetchChats = () => {
            axios.get<GetApiPaginationGeneric<ChatType>>(`${API_URL}/api/chats?page=1&size=50`, {withCredentials: true})
                .then((res) => {
                    setChats(res.data.items);
                })
                .catch(err => console.log(err))
                .finally(() => setIsLoading(false));
        }

        fetchChats();

    }, [])


    return (
        <>
            <Header/>
            <div className={styles.wrapper}>
                <div className={styles.title}>Chats</div>
                {isLoading ? <div>Loading...</div> : chats.map((chat: ChatType) => <Chat
                    profile_image={chat.profile_picture} username={chat.username} last_message={chat.last_message}
                    user_id={chat.user_id}/>)}
            </div>
        </>
    )
}

export default Chats