import { useRef } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, useScroll, useTransform } from 'framer-motion';
import Card from './card/card';

import useMediaQuery from '../../../hooks/useMediaQuery';

import styles from './teamSection.module.css';

const TeamSection = ({ members }) => {
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start']
    });

    const isDesktop = useMediaQuery('(min-width: 1280px)');
    const range = isDesktop ? ['-20%', '40%'] : ['-10%', '-20%'];

    const y = useTransform(scrollYProgress, [0, 1], range);

    return (
        <div ref={ref} className={styles.teamSection}>
            <motion.div style={{ y }} className={styles.team}>
                {members.map((member, index) => (
                    <Card
                        key={index}
                        headline={member.headline}
                        img={member.img}
                        name={member.name}
                    />
                ))}
            </motion.div>
        </div>
    );
};

export default TeamSection;