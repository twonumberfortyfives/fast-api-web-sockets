import React from "react";
import Header from "../../components/header/header.tsx";
import NotFound from "../../components/notFound/notFound.tsx";

const Error:React.FC = () => {
    return (
        <>
            <Header/>
            <NotFound/>
        </>
    );
};

export default Error;