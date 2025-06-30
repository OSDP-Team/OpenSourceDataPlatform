import React, { useRef } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, useScroll, useTransform } from 'framer-motion';
import pic from '../../assets/header.jpg'
import styles from './Header.module.css'; 

function Header({ headline, subheadline }) {
  const ref = useRef(null);

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end start'], 
  });

  const mainHeadlineOpacity = useTransform(
    scrollYProgress,
    [0, 0.1], 
    [1, 0]    
  );

  const mainHeadlineY = useTransform(
    scrollYProgress,
    [0, 0.1],
    [0, -50]
  );

  const subHeadlineOpacity = useTransform(
    scrollYProgress,
    [0.05, 0.15], 
    [0, 1]        
  );

  const subHeadlineY = useTransform(
    scrollYProgress,
    [0.05, 0.15],
    [50, 0]
  );


  return (
    <div ref={ref} className={styles.wrapper}>
      <div 
        className={styles.stickyBackground}
        style={{ backgroundImage: `url(${ pic })` }}
      >
        {}
        <div className={styles.headlines}>
          <motion.h1
            style={{
              opacity: mainHeadlineOpacity,
              y: mainHeadlineY,
            }}
          >
            {headline}
          </motion.h1>

          <motion.h2
            style={{
              opacity: subHeadlineOpacity,
              y: subHeadlineY,
            }}
          >
            {subheadline}
          </motion.h2>
        </div>

      </div>
      {}
      <div className={styles.scrollSpacer}></div> 
    </div>
  );
}

export default Header;