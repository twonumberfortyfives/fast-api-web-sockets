import React, { useEffect, useState } from "react";
import Header from "../../components/header/header.tsx";
import styles from "./searchPost.module.css";
import axios from "axios";
import NotFound from "../../components/notFound/notFound.tsx";
import Post from "../../components/post/post.tsx";
import User from "../../components/user/user.tsx";
import { useSelector } from "react-redux";
import { RootState } from "../../redux/store.ts";
import { GetApiPaginationGeneric, PostType, UserType } from "../../types/types.ts";
import {API_URL} from "../../config.ts";

const SearchPost: React.FC = () => {
    const [posts, setPosts] = useState<PostType[]>([]);
    const [users, setUsers] = useState<UserType[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [fetching, setFetching] = useState(true);
    const searchText = useSelector((state: RootState) => state.search.value);
    const [debouncedSearchText, setDebouncedSearchText] = useState(searchText);
    const isUserSearch = debouncedSearchText.startsWith("@");

    useEffect(() => {
        const timeout = setTimeout(() => {
            setDebouncedSearchText(searchText);
        }, 300);

        return () => {
            clearTimeout(timeout);
        };
    }, [searchText]);

    useEffect(() => {
        setPosts([]);
        setUsers([]);
        setCurrentPage(1);
        setFetching(true);
        setIsLoading(true);
    }, [debouncedSearchText]);

    useEffect(() => {
        const fetchItems = (): void => {
            const url = isUserSearch
                ? `${API_URL}/api/users/${debouncedSearchText.slice(1)}?size=10&page=${currentPage}`
                : `${API_URL}/api/posts/${debouncedSearchText}?size=5&page=${currentPage}`;

            axios.get<GetApiPaginationGeneric<PostType | UserType>>(url, { withCredentials: true })
                .then((res) => {
                    if (currentPage === 1) {
                        if(isUserSearch){
                            console.log(res.data.items)
                            setUsers(res.data.items as UserType[])
                        } else {
                            setPosts(res.data.items as PostType[]);
                        }
                    } else {
                        if(isUserSearch){

                            setUsers((prevUsers) => [...prevUsers, ...(res.data.items as UserType[])])
                        } else {
                            setPosts((prevPosts) => [...prevPosts, ...(res.data.items as PostType[])]);
                        }
                    }
                    setTotalCount(res.data.total);
                })
                .finally(() => {
                    setIsLoading(false);
                    setFetching(false);
                });
        };

        if (fetching) {
            fetchItems();
        }
    }, [fetching, currentPage, debouncedSearchText, isUserSearch]);

    useEffect(() => {
        const handleScroll = (e: Event) => {
            const target = e.target as Document;
            const scrollPosition = target.documentElement.scrollHeight - (target.documentElement.scrollTop + window.innerHeight);

            if (scrollPosition < 200 && (isUserSearch ? users.length : posts.length) < totalCount && !fetching) {
                setFetching(true);
                setCurrentPage((prevPage) => prevPage + 1);
            }
        };

        document.addEventListener("scroll", handleScroll);
        return () => {
            document.removeEventListener("scroll", handleScroll);
        };
    }, [posts, users, totalCount, fetching, isUserSearch]);

    return (
        <>
            <Header />
            <div className={styles.wrapper}>
                {isLoading ? (
                    <div>Loading...</div>
                ) : (
                    isUserSearch ? (
                        users.length > 0 ? (
                            users.map((user: UserType, index) => (
                                <User
                                    key={index}
                                    username={user.username}
                                    profile_picture={user.profile_picture}
                                    id={user.id}
                                />
                            ))
                        ) : (
                            <NotFound />
                        )
                    ) : (
                        posts.length > 0 ? (
                            posts.map((post: PostType, index) => (
                                <Post
                                    key={index}
                                    topic={post.topic}
                                    author={{
                                        username: post.user.username,
                                        id: post.user.id,
                                        profile_picture: post.user.profile_picture,
                                    }}
                                    tags={post.tags}
                                    info={{ likes: post.likes_count, comments: post.comments_count }}
                                    isLiked={post.is_liked}
                                    id={post.id}
                                    created_at={post.created_at}
                                />
                            ))
                        ) : (
                            <NotFound />
                        )
                    )
                )}
            </div>
        </>
    );
};

export default SearchPost;
