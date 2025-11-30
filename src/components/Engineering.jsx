import React from 'react';

const Engineering = ({ projects }) => {
    return (
        <section id="engineering" className="section">
            <div className="container">
                <h2 className="section_title">Engineering Projects</h2>
                <div className="grid grid--cols-1">
                    {projects.map((project, index) => (
                        <div key={index} className="engineering-card">
                            {project.link ? <a href={project.link} className="engineering-card_title">{project.title}</a> : <p className="engineering-card_title">{project.title}</p>}

                            <div className="engineering-card_summary">
                                <p>{project.summary}</p>
                            </div>

                            <div className="tech-stack">
                                {project.tech.map((t, i) => (
                                    <span key={i} className="tech-tag">
                                        {t}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Engineering;
