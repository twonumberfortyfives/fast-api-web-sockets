import React, {useEffect, useRef, useState} from "react";
import styles from "./header.module.css";
import {Link, useLocation, useNavigate} from "react-router-dom";
import homeImage from "../../assets/home.svg";
import messageImage from "../../assets/message.svg";
import searchImage from "../../assets/search_icon.svg";
import groupImage from "../../assets/group.svg";
import aboutUsImg from "../../assets/about-us.svg";
import expandArrow from "../../assets/expand-arrow.svg"
import logo from "../../assets/logo.svg"
import {useDispatch, useSelector} from "react-redux";
import {RootState} from '../../redux/store';
import useAuth from "../../hooks/useAuth.ts";
import {setSearchValue} from "../../redux/slices/searchSlice.ts";
import {logout} from "../../redux/slices/userSlice.ts";
import axios from "axios";
import {API_URL} from "../../config.ts";

const Header: React.FC = () => {
    const user = useSelector((state: RootState) => state.user.user);
    const isAuthenticated = useAuth();

    const searchText = useSelector((state: RootState) => state.search.value);
    const inputRef = useRef<HTMLInputElement | null>(null);
    const navigate = useNavigate();
    const location = useLocation();
    const dispatch = useDispatch();
    const [isActive, setIsActive] = useState(false);
    const popUpRef = useRef<HTMLDivElement>(null);

    const handleInput = (e: React.ChangeEvent<HTMLInputElement>): void => {
        dispatch(setSearchValue(e.target.value));
        if (location.pathname !== "/search-posts" && e.target.value !== "") {
            navigate("/search-posts", {state: {focus: true}});
            return
        }
        if (e.target.value === "") {
            dispatch(setSearchValue(""));
            navigate("/", {state: {focus: true}});
        }
    };

    useEffect(() => {
        if (location.state?.focus) {
            navigate(location.pathname, {replace: true, state: {focus: false}});
            inputRef.current?.focus();
        }
    }, [location.pathname, location.state?.focus, navigate]);
    
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (popUpRef.current && !popUpRef.current.contains(e.target as Node)) {
                setIsActive(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        }
    });

    const handlePopUpButton = () => {
        setIsActive(!isActive);
    }

    const handleLogoutButton = () => {
        axios.post(`${API_URL}/api/logout`, {}, {withCredentials: true}).then(() => {
            dispatch(logout());
            navigate("/login");
        })
    }

    return (
        <header className={styles.wrapper}>
            <div className={styles.logo_and_nav}>
                <div className={styles.logo}>
                    <span className={styles.logo__img}>
                        <img src={logo} alt="logo"/>
                    </span>
                    <div className={styles.logo__text}>Agora</div>
                </div>
                <nav className={styles.links}>
                    <Link to={"/"} className={styles.link_wrapper}>
                        <img src={homeImage} alt="home link"/>
                    </Link>
                    <Link to={"/users"} className={styles.link_wrapper}>
                        <img src={groupImage} alt="groups link"/>
                    </Link>
                    <Link to={"/about-us"} className={styles.link_wrapper}>
                        <img src={aboutUsImg} alt="about us link"/>
                    </Link>
                </nav>
            </div>
            <div className={styles.search_wrapper}>
                <input
                    ref={inputRef}
                    value={searchText}
                    onChange={handleInput}
                    placeholder="Type here to search..."
                    className={styles.search}
                    type="text"
                    maxLength={40}
                    autoComplete={"off"}
                />
                <Link to={"/search-posts"} className={styles.search__button}>
                    <img className={styles.search__button__img} src={searchImage} alt="search"/>
                </Link>
            </div>
            {isAuthenticated ? (
                <div className={styles.profile_wrapper}>
                    {/*<Link to={"/"} className={styles.profile__link}>
                        <img src={notificationImage} alt="notifications link"/>
                    </Link>*/}
                    <Link to={"/chats"} className={styles.profile__link}>
                        <img src={messageImage} alt="messages link"/>
                    </Link>
                    <div ref={popUpRef} className={`${styles.profile} ${isActive ? styles.active : ""}`}>
                        <img width={36} height={36} className={styles.profile__img} src={user?.profile_picture}
                             alt="profile"/>
                        <Link to={"/profile"} className={styles.profile__name}>
                            {user?.username}
                        </Link>
                        <button onClick={handlePopUpButton} className={styles.profile__pop_up_button}><img
                            className={styles.profile__pop_up__img} src={expandArrow} alt="expand arrow"/></button>
                        <div className={styles.pop_up_wrapper}>
                            <div className={styles.line}></div>
                            <Link to={"/edit-profile"}>Edit profile</Link>
                            <Link to={"/settings"}>Settings</Link>
                            <button onClick={handleLogoutButton}>Logout</button>
                        </div>
                    </div>
                </div>
            ) : (
                <div className={styles.login}>
                    <Link className={styles.login__button} to={"/login"}>
                        Login
                    </Link>
                    <span className={styles.separator}> | </span>
                    <Link className={styles.login__button} to={"/register"}>
                        Register
                    </Link>
                </div>
            )}
        </header>
    );
};

export default Header;
