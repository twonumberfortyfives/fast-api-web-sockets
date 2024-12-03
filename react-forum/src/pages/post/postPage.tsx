import React, {useEffect, useState} from "react";
import Header from "../../components/header/header.tsx";
import styles from "./postPage.module.css";
import likeActiveImage from "../../assets/like-active.svg";
import likeImage from "../../assets/like.svg";
import editImage from "../../assets/edit.svg";
import removeImage from "../../assets/remove.svg";
import {Link, useNavigate, useParams} from "react-router-dom";
import axios from "axios";
import NotFound from "../../components/notFound/notFound.tsx";
import useTimeAgo from "../../hooks/useTimeAgo.ts";
import {GetApiPaginationGeneric, PostType} from "../../types/types.ts";
import Tag from "../../components/post/tag/tag.tsx";
import {useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import ConfirmationModal from "../../components/confirmationModal/confirmationModal.tsx";
import useAuth from "../../hooks/useAuth.ts";
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import Comments from "./comments/comments.tsx";
import ImageViewer from "../../components/imageViewer/imageViewer.tsx"
import {API_URL} from "../../config.ts";

const PostPage: React.FC = () => {
    const {id} = useParams();
    const [post, setPost] = useState<PostType | null>(null);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setModalOpen] = useState(false);
    const [confirmationModalOpen, setConfirmationModalOpen] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const timeAgo = useTimeAgo(post?.created_at || "")

    const userId = useSelector((state: RootState) => state.user.user?.id);
    const navigate = useNavigate();
    const isAuth = useAuth();

    useEffect(() => {
        if (loading) {
            axios.get<GetApiPaginationGeneric<PostType>>(`${API_URL}/api/posts/${id}`, {withCredentials: true}).then(res => {
                setPost(res.data.items[0]);
            }).finally(() => setLoading(false));
        }
    }, [loading, id]);

    const deletePost = async () => {
        try {
            await axios.delete(`${API_URL}/api/posts/${id}`, {withCredentials: true});
            navigate("/");
        } catch (err) {
            console.log(err);
        }
    };

    const handleLikeButton = () => {
        if (!isAuth) return;
        if (post?.is_liked) {
            axios.delete(`${API_URL}/api/posts/${id}/like/`, {withCredentials: true}).then(() => {
                setPost(prevState => {
                    if (prevState) {
                        return {
                            ...prevState,
                            likes_count: prevState.likes_count - 1,
                            is_liked: false,
                        };
                    }
                    return prevState;
                });

            })
        } else {
            axios.post(`${API_URL}/api/posts/${id}/like/`, {}, {withCredentials: true}).then(() => {
                setPost(prevState => {
                    if (prevState) {
                        return {
                            ...prevState,
                            likes_count: prevState.likes_count + 1,
                            is_liked: true,
                        };
                    }
                    return prevState;
                });

            })
        }
    };

    const openImageViewer = (index: number) => {
        setCurrentImageIndex(index);
        setModalOpen(true);
    }

    return (
        <>
            <Header/>

            {loading ? (
                <div>Loading...</div>
            ) : (
                post ? (
                    <div className={styles.wrapper}>
                        <div className={styles.post}>
                            <div className={styles.nav}>
                                {post.user.id === userId && (
                                    <>
                                        <button onClick={() => navigate(`/edit-post/${id}`)}
                                                className={styles.nav__button}>
                                            <img className={styles.nav__button__img} src={editImage} alt="edit"/>
                                        </button>
                                        <button onClick={() => setConfirmationModalOpen(true)} className={styles.nav__button}>
                                            <img className={styles.nav__button__img} src={removeImage} alt="delete"/>
                                        </button>
                                    </>
                                )}
                                <button onClick={handleLikeButton} className={styles.nav__button}>
                                    <img className={styles.nav__button__img}
                                         src={post.is_liked ? likeActiveImage : likeImage} alt="like"/>
                                </button>
                            </div>
                            <div className={styles.topic}>{post.topic.trim()}</div>
                            {post.files.length > 0 ? <div className={styles.images}>
                                {post.files.map((file,index) => (
                                    <img
                                        className={styles.images_img}
                                        key={index}
                                        src={file.link}
                                        alt=""
                                        onClick={() => openImageViewer(index)}
                                    />
                                ))}
                            </div>: null}
                            <div className={styles.description}>
                                <ReactMarkdown remarkPlugins={[remarkBreaks]}>{post.content.trim()}</ReactMarkdown>
                            </div>
                            <div className={styles.tags}>
                                {post.tags.map((tag) => <Tag key={tag} tag={tag}/>)}
                            </div>
                            <div className={styles.line}/>
                            <div className={styles.post_footer}>
                                <div className={styles.author}>
                                    <img src={post.user.profile_picture} alt="" className={styles.author__img}/>
                                    <div className={styles.author__info}>
                                        <Link className={styles.author__name} to={`/profile/${post.user.id}`}>
                                            {post.user.username}
                                        </Link>
                                        <div className={styles.author__date}>{timeAgo}</div>
                                    </div>
                                </div>
                                <div className={styles.info}>
                                    <div className={styles.info__field}>{post.likes_count} Likes</div>
                                    <div className={styles.info__field}>{post.comments_count} Comments</div>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : <NotFound/>
            )}

            <ConfirmationModal
                text="Are you sure you want to delete this post?"
                isOpen={confirmationModalOpen}
                onClose={() => setConfirmationModalOpen(false)}
                onConfirm={deletePost}
            />

            {post ? (
                <Comments setPost={setPost} id={post.id} authorId={post.user.id}/>
            ) : null}

            {isModalOpen && post && (
                <ImageViewer
                    images={post.files.map(file => file.link)}
                    initialIndex={currentImageIndex}
                    onClose={() => setModalOpen(false)}
                />
            )}
        </>
    );
};

export default PostPage;
