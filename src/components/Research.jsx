import React from 'react';
import { Download } from 'lucide-react';

const Research = ({ projects }) => {
    return (
        <section id="research" className="section section--alt">
            <div className="container">
                <h2 className="section_title">Research</h2>
                <div className="project-list">
                    {projects.map((project, index) => (
                        <div key={index} className="research-card">
                            <div className="research-card_header">
                                <h3 className="research-card_title">
                                    {project.link ? <a href={project.link}>{project.title}</a> : project.title}
                                </h3>
                                <span className="research-card_status">{project.status}</span>
                            </div>
                            <p className="research-card_role">{project.role}</p>

                            <div className="research-card_summary">
                                <p>{project.summary}</p>
                            </div>

                            <div className="research-card_footer">
                                <div className="tech-stack">
                                    {project.tech.map((t, i) => (
                                        <span key={i} className="tech-tag">{t}</span>
                                    ))}

                                    {/* space filling div */}
                                    <div className="spacer"></div>

                                    {project.documents && project.documents.length > 0 && (
                                        <div className="document-list">
                                            {project.documents.map((doc, i) => (
                                                <a key={i} href={doc.url} className="document-link" download>
                                                    <Download size={14} />
                                                    {doc.name}
                                                </a>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Research;
