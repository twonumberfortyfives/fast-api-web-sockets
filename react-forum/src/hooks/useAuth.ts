import {useEffect} from 'react';
import axios from 'axios';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../redux/store';
import {login, notAuthorized} from "../redux/slices/userSlice.ts";
import {API_URL} from "../config.ts";

const useAuth = (): boolean | null => {

    const isAuthenticated = useSelector((state: RootState) => state.user.isAuthenticated);
    const dispatch = useDispatch();

    useEffect(() => {

        const checkAuthentication = async (): Promise<void> => {
            if (isAuthenticated !== null) return;
            try {
                const profile = await axios.get(`${API_URL}/api/my-profile`, { withCredentials: true, headers:{"Access-Control-Allow-Origin":"https://opiskelija9.amiskoodari.fi"}});
                dispatch(login(profile.data));
            } catch {
                dispatch(notAuthorized())
            }
        };

        if (isAuthenticated === null) {
            checkAuthentication();
        }
    }, [isAuthenticated, dispatch]);

    return isAuthenticated;
};

export default useAuth;
