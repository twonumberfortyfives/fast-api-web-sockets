import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {UserType} from "../../types/types.ts";

interface AuthState {
    isAuthenticated: boolean | null;
    user: null | UserType;
}

const initialState: AuthState = {
    isAuthenticated: null,
    user: null,
};

const userSlice = createSlice({
    name: 'user',
    initialState,
    reducers: {
        login(state, action: PayloadAction<UserType>) {
            state.isAuthenticated = true;
            state.user = action.payload;
        },
        logout(state) {
            state.isAuthenticated = false;
            state.user = null;
        },
        notAuthorized(state){
            state.isAuthenticated = false;
        }
    },
});

export const {login, logout, notAuthorized} = userSlice.actions;
export default userSlice.reducer;
