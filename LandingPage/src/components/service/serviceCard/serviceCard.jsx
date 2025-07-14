import styles from './serviceCard.module.css';

const ServiceCard = ({ img, headline, text, path, buttonName }) => {
    return (
        <div className={styles.wrapper}>
            <img src={img} alt="icon" />
            <h3>{headline}</h3>
            <p>{text}</p>
            <a 
                href={path}
                target="_blank" 
                rel="noopener noreferrer"
                className={styles.button}
            >
                {buttonName}
            </a>
        </div>
    )
}

export default ServiceCard;