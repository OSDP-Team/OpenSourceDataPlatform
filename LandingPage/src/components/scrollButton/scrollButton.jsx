import { useEffect, useState } from "react";
import { FaArrowUp } from "react-icons/fa";
import styles from './scrollButton.module.css';

const ScrollButton = () => {
    const [visible, setVisible] = useState(false);

    const toggleVisibility = () => {
        if (window.scrollY > 300) {
            setVisible(true);
        } else {
            setVisible(false);
        }
    };

    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    };

    useEffect( () => {
        window.addEventListener("scroll", toggleVisibility);
        return () => window.removeEventListener("scroll", toggleVisibility);
    }, []);

    return (
        <button
            onClick={scrollToTop}
            className={`${styles.ScrollButton} ${visible ? styles.Visible : ""}`}
        >
            <FaArrowUp size={20} />
        </button>
    )
}

export default ScrollButton;