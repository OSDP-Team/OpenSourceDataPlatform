import styles from './separator.module.css';

const Separator = ({ imageUrl }) => {
    const sectionStyle = {
        backgroundImage: `url(${imageUrl})`
    };

    return (
        <div 
            className={styles.parallaxWindow} 
            style={sectionStyle}
            role="img"
            aria-label="Trenn-Bild mit Parallax-Effekt"
        />
    );
};

export default Separator;