interface FileType {
    id:number,
    link:string,
}

export interface PostType {
    "id": number,
    "topic": string,
    "content": string,
    "created_at": string,
    "files": FileType[],
    "tags": string[],
    "likes_count": number,
    comments_count: number,
    "is_liked": boolean,
    "user": {
        "id": number,
        "username": string,
        "email": string,
        "profile_picture": string,
    }
}



export interface CommentType {
    id: number;
    user_id: number;
    user_email: string;
    username: string;
    profile_picture: string;
    content: string;
    created_at: string;
}

export interface UserType {
    id: number;
    username: string;
    email: string;
    profile_picture:string;
    bio: string;
}

export interface GetApiPaginationGeneric<itemsType> {
    items: itemsType[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface ChatType{
    id: number;
    user_id: number;
    name: string;
    username: string;
    profile_picture: string;
    last_message: string;
    created_at: string;
}

export interface MessageType {
    id: number,
    conversation_id: number,
    created_at: string,
    user_id: number,
    content: string,
    username: string,
    profile_picture:string,
    files: {link: string, id: number}[],
}