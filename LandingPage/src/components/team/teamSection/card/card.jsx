import styles from './card.module.css';

const Card = ({ headline, img, name }) => {
    return (
        <div className={styles.wrapper}>
            <h4>
                {headline}
            </h4>
            <div className={styles.contentWrapper}>
                <div className={styles.imgWrapper}>
                    <img src={img} alt="Person" />
                </div>
                <span>{name}</span>
            </div>
        </div>
    )
}

export default Card;