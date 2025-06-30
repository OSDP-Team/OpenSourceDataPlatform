import { useRef } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, useScroll, useTransform } from 'framer-motion';
import img from '../../assets/dummy.png'

import useMediaQuery from '../../hooks/useMediaQuery'

import styles from './intro.module.css';

const Intro = ({ headline, text }) => {
    const ref = useRef(null);
    const { scrollYProgress } =useScroll({
        target: ref,
        offset: ['start end', 'end start']
    });

    const isDesktop = useMediaQuery('(min-width: 1115px)');
    const rangey = isDesktop ? ['-50%', '70%'] : ['0%', '0%'];
    const rangex = isDesktop ? ['20%', '-40%'] : ['0%', '0%'];
    
    const y = useTransform(scrollYProgress, [0, 1], rangey);
    const x = useTransform(scrollYProgress, [0, 1], rangex);

    const motionStyle = {
        y: y,
        ...(isDesktop && {
            translateX: "50%",
            translateY: "-50%"
        })
    };

    return (
        <div className={styles.wrapper}>
            <motion.div
                className={styles.contentWrapper}
                style={motionStyle}
            >
                <h3>{headline}</h3>
                <p>{text}</p>
            </motion.div>
            <div className={styles.imgWrapper}>
                <motion.img 
                    className={styles.Img}
                    src={img}
                    alt='Img'
                    style={{ x }}
                />
            </div>
        </div>
    )
}

export default Intro;