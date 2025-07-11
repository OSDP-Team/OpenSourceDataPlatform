import { useRef } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, useScroll, useTransform } from 'framer-motion';
import TeamSection from './teamSection/teamSection';

import dummy from '../../assets/dummy.png';
import simon from '../../assets/team/simon.jpg';
import sven from '../../assets/team/sven.jpg';
import daniel from '../../assets/team/daniel.png';
import jerome from '../../assets/team/jerome.jpeg';
import lars from '../../assets/team/lars.jpeg';
import leart from '../../assets/team/leart.jpeg';
import nico from '../../assets/team/nico.jpeg';

import styles from './team.module.css';

const teamsData = [
    {
        members: [
            { headline: "Ansprechperson", name: "Rainer Duda", img: dummy },
            { headline: "Projektleiter", name: "Simon Kerler", img: simon },
            { headline: "Betreuer", name: "Dr. Prof. Heindl", img: dummy },
        ]
    },
    {
        members: [
            { headline: "Developer", name: "Nico Eberhardt", img: nico },
            { headline: "Developer", name: "Sven Plasch", img: sven },
            { headline: "Developer", name: "Leart Gashi", img: leart },
        ]
    },
    {
        members: [
            { headline: "Dashboard", name: "Lars Butschle", img: lars },
            { headline: "Dokumentation", name: "Jerome Durmus", img: jerome },
            { headline: "Projektmanagm.", name: "Daniel Kixmüller", img: daniel },
        ]
    }
];

const Team = () => {
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start start', 'end end']
    });

    const opacityPj = useTransform(scrollYProgress, [0, 0.01, 0.25, 0.33], [0, 1, 1, 0]);
    const opacityDev = useTransform(scrollYProgress, [0.33, 0.4, 0.58, 0.66], [0, 1, 1, 0]);
    const opacityData = useTransform(scrollYProgress, [0.66, 0.75, 1], [0, 1, 1]);
    
    const yPj = useTransform(scrollYProgress, [0.25, 0.33], ['0%', '-50%']);
    const yDev = useTransform(scrollYProgress, [0.33, 0.4, 0.58, 0.66], ['50%', '0%', '0%', '-50%']);
    const yData = useTransform(scrollYProgress, [0.66, 0.75], ['50%', '0%']);

    return (
        <div ref={ref} className={styles.wrapper}>
            <h2 className={styles.mainHeadline}>Unser Team</h2>
            <div className={styles.contentGrid}>
                <div className={styles.stickyHeadlineContainer}>
                    <motion.h3 style={{ opacity: opacityPj, y: yPj }}>Projektleitung</motion.h3>
                    <motion.h3 style={{ opacity: opacityDev, y: yDev }}>Dev-Team</motion.h3>
                    <motion.h3 style={{ opacity: opacityData, y: yData }}>Data-Team</motion.h3>
                </div>
                <div className={styles.scrollingTeamsContainer}>
                    {teamsData.map((team, index) => (
                        <TeamSection key={index} members={team.members} />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Team;
