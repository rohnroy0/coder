import React from 'react';

export const DifficultyBadge = ({ difficulty }) => {
  const diff = (difficulty || 'EASY').toUpperCase();

  const styles = {
    EASY: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200',
    HARD: 'bg-rose-50 text-rose-700 border-rose-200',
  };

  const currentStyle = styles[diff] || styles.EASY;

  return (
    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${currentStyle}`}>
      {diff}
    </span>
  );
};

export default DifficultyBadge;
