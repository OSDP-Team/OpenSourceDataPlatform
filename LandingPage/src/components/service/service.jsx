// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import ServiceCard from './serviceCard/serviceCard';
import styles from './service.module.css';

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.2 
        }
    }
};

const itemVariants = {
    hidden: { scale: 0.8, opacity: 0 },
    visible: {
        scale: 1,
        opacity: 1,
        transition: {
            duration: 0.5
        }
    }
};


const Service = ({ servicesData, sectionTitle }) => {
    return (
        <section className={styles.wrapper}>
            <h2 className={styles.sectionHeadline}>{sectionTitle}</h2>
            <motion.div
                className={styles.cardContainer}
                variants={containerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, amount: 0.2 }}
            >
                {servicesData.map((service, index) => (
                    <motion.div 
                        key={index} 
                        variants={itemVariants} 
                        className={styles.cardWrapper}
                    >
                        <ServiceCard
                            img={service.img}
                            headline={service.headline}
                            text={service.text}
                            path={service.path}
                            buttonName={service.buttonName}
                        />
                    </motion.div>
                ))}
            </motion.div>
        </section>
    );
};

export default Service;