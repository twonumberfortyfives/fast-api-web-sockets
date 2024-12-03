import React, {useEffect, useState} from "react";
import {GetApiPaginationGeneric, PostType} from "../../types/types.ts";
import axios from "axios";
import Post from "../post/post.tsx";

type PropsType = {
    link: string;
}

const PostsPagination: React.FC<PropsType> = ({link}: PropsType) => {

    const [posts, setPosts] = useState<PostType[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [fetching, setFetching] = useState(true);
    const [totalCount, setTotalCount] = useState(0);

    useEffect(() => {
        const fetchPosts = (): void => {
            axios.get<GetApiPaginationGeneric<PostType>>(`${link}?size=5&page=${currentPage}`, {withCredentials: true})
                .then((res) => {
                    if (currentPage === 1) {
                        setPosts(res.data.items);
                    } else {
                        setPosts((prevPosts) => [...prevPosts, ...res.data.items]);
                    }
                    setTotalCount(res.data.total);
                })
                .finally(() => {
                    setIsLoading(false);
                    setFetching(false);
                });
        };

        if (fetching) {
            fetchPosts();
        }
    }, [fetching, currentPage, link]);

    useEffect(() => {
        const handleScroll = (e: Event) => {
            const target = e.target as Document;
            const scrollPosition = target.documentElement.scrollHeight - (target.documentElement.scrollTop + window.innerHeight);

            if (scrollPosition < 200 && posts.length < totalCount && !fetching) {
                setFetching(true);
                setCurrentPage((prevPage) => prevPage + 1);
            }
        };

        document.addEventListener("scroll", handleScroll);
        return () => {
            document.removeEventListener("scroll", handleScroll);
        };
    }, [posts, totalCount, fetching]);

    return (
        <>
            {isLoading ?
                <div>Loading...</div>
                :
                posts.map((post) => (
                    <Post
                        key={post.id}
                        topic={post.topic}
                        author={{
                            username: post.user.username,
                            id: post.user.id,
                            profile_picture: post.user.profile_picture,
                        }}
                        tags={post.tags}
                        info={{likes: post.likes_count, comments: post.comments_count}}
                        isLiked={post.is_liked}
                        id={post.id}
                        created_at={post.created_at}
                    />
                ))
            }
        </>
    )
}

export default PostsPagination;