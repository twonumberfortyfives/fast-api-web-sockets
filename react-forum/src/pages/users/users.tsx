import styles from "./users.module.css"
import React, {useEffect, useState} from "react";
import Header from "../../components/header/header.tsx";
import axios from "axios";
import {API_URL} from "../../config.ts";
import {GetApiPaginationGeneric, UserType} from "../../types/types.ts";
import User from "../../components/user/user.tsx";
import NotFound from "../../components/notFound/notFound.tsx";

const Users: React.FC = () => {

    const [isLoading, setIsLoading] = useState(true);
    const [fetching, setFetching] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [users, setUsers] = useState<UserType[]>([]);
    useEffect(() => {
        const fetchUsers = () => {
            axios.get<GetApiPaginationGeneric<UserType>>(`${API_URL}/api/users?size=10&page=${currentPage}`)
                .then((res) => {
                    setUsers(prevState => [...prevState, ...res.data.items]);
                    setTotalCount(res.data.total);
                    setIsLoading(false);
                    setFetching(false);
                })
        }

        if (fetching) {
            fetchUsers();
        }
    }, [currentPage, fetching]);

    useEffect(() => {
        const handleScroll = (e: Event) => {
            const target = e.target as Document;
            const scrollPosition = target.documentElement.scrollHeight - (target.documentElement.scrollTop + window.innerHeight);

            if (scrollPosition < 200 && users.length < totalCount && !fetching) {
                setFetching(true);
                setCurrentPage((prevPage) => prevPage + 1);
            }
        };

        document.addEventListener("scroll", handleScroll);
        return () => {
            document.removeEventListener("scroll", handleScroll);
        };
    }, [users, totalCount, fetching]);

    return (
        <>
            <Header/>
            <div className={styles.wrapper}>
                {isLoading ? <div>Loading...</div> : users.length > 0 ? (
                    users.map((user: UserType, index) => (
                        <User
                            key={index}
                            username={user.username}
                            profile_picture={user.profile_picture}
                            id={user.id}
                        />
                    ))
                ) : (
                    <NotFound/>
                )}
            </div>
        </>
    )
}

export default Users;