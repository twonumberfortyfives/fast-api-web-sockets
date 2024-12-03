import Header from "../../components/header/header.tsx";
import styles from "./editProfile.module.css"
import React, {useEffect, useRef, useState} from "react";
import useAuth from "../../hooks/useAuth.ts";
import {useNavigate} from "react-router-dom";
import {useDispatch, useSelector} from "react-redux";
import {RootState} from "../../redux/store.ts";
import axios from "axios";
import {login} from "../../redux/slices/userSlice.ts";
import {UserType} from "../../types/types.ts";
import {API_URL} from "../../config.ts";

const EditProfile: React.FC = () => {

    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const [imageSrc, setImageSrc] = useState<string | null>(null);
    const [name, setName] = useState("");
    const [bio, setBio] = useState("");
    const [error, setError] = useState("");
    const user = useSelector((state: RootState) => state.user.user);
    const navigate = useNavigate();
    const isAuthenticated = useAuth();
    const dispatch = useDispatch()

    const handleUploadFileButton = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    }

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setFile(file)
            const reader = new FileReader();
            reader.onload = (e) => {
                const result = e.target?.result as string;
                setImageSrc(result);
            };
            reader.readAsDataURL(file);
        }
    };

    useEffect(() => {
        if (isAuthenticated === false) {
            navigate("/login");
            return
        }
        if (user) {
            setName(user.username);
            setBio(user.bio ? user.bio : "");
        }
    }, [user, isAuthenticated, navigate]);

    const handleChangeNameInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setName(e.target.value);
    }

    const handleChangeBioInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setBio(e.target.value);
    }

    const handleConfirmButton = () => {
        setError("")
        const formData = new FormData();
        if (file) {
            formData.append("profile_picture", file);
        } else {
            formData.append("profile_picture", "");
        }

        let queryString = "";

        if (name !== user?.username) {
            if (name.length < 2 || name.length > 20) {
                setError("Username must be between 3 and 20 characters");
                return;
            }
            queryString += `&username=${encodeURIComponent(name)}`;
        }

        if (bio !== user?.bio) {
            if (bio.length > 200) {
                setError("Bio must be less than 200 characters");
                return;
            }
            queryString += `&bio=${encodeURIComponent(bio)}`;
        }

        if (formData.get("profile_picture") === "" && queryString === "") {
            navigate("/profile");
            return;
        }

        axios.patch<UserType>(`${API_URL}/api/my-profile?${queryString}`, formData, {
            withCredentials: true, headers: {
                "Content-Type": "multipart/form-data",
            }
        }).then((response) => {
            if (user) {
                dispatch(login(response.data));
                navigate("/profile");
            }
        }).catch(() => {
            setError("Incorrect data");
        })

    }

    return (
        <>
            <Header/>
            <div className={styles.wrapper}>
                {error ? <div className={styles.error}>{error}</div> : null}
                <div className={styles.profile}>
                    <button onClick={handleUploadFileButton} className={styles.upload_button}>
                        {imageSrc ? <img height={200} width={200} className={styles.editImage__image} src={imageSrc}
                                         alt="profile"/> :
                            <img height={200} width={200} className={styles.editImage__image}
                                 src={user?.profile_picture}
                                 alt="profile"/>}
                    </button>
                    <input onChange={handleFileChange} ref={fileInputRef} style={{display: "none"}} type="file"
                           accept="image/*"/>
                    <div className={styles.profile__info}>
                        <input onChange={handleChangeNameInput} type="text" value={name}
                               className={styles.profile__name}/>
                        <textarea onChange={handleChangeBioInput} value={bio} placeholder="Bio"
                                  className={styles.profile__bio}/>
                    </div>
                </div>
                <div className={styles.buttons}>
                    <button onClick={() => {
                        navigate(-1)
                    }} className={styles.cancel}>Cancel
                    </button>
                    <button onClick={handleConfirmButton} className={styles.confirm}>Save</button>
                </div>
            </div>
        </>
    )
}

export default EditProfile