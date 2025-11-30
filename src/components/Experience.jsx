import React from 'react';

const Experience = ({ teaching, industry }) => {
    return (
        <section id="experience" className="section section--alt">
            <div className="container">
                <div className="grid grid--cols-2">
                    <div>
                        <h2 className="section_title">Teaching</h2>
                        <div className="experience-list">
                            {teaching.map((exp, index) => (
                                <div key={index} className="experience-card">
                                    <h4 className="experience-card_title">{exp.course}</h4>
                                    <p className="experience-card_meta">{exp.institution} | {exp.role}</p>
                                    <p className="experience-card_description">{exp.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div>
                        <h2 className="section_title">Industry</h2>
                        <div className="experience-list">
                            {industry.map((exp, index) => (
                                <div key={index} className="experience-card">
                                    <h4 className="experience-card_title">{exp.company}</h4>
                                    <p className="experience-card_meta">{exp.team} | {exp.role}</p>
                                    <p className="experience-card_description">{exp.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Experience;
