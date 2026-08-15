\# HR Self-Correcting RAG Assistant



A retrieval-augmented HR policy assistant that combines semantic retrieval, self-correction, query rewriting, and a learned halting policy.



\## Architecture



```text

User

&#x20; |

&#x20; v

Web Frontend

&#x20; |

&#x20; v

FastAPI /ask

&#x20; |

&#x20; v

SentenceTransformer Embedding

&#x20; |

&#x20; v

ChromaDB Retrieval

&#x20; |

&#x20; v

Local Retrieval Critic

&#x20; |

&#x20; +---- SUFFICIENT ----> STOP

&#x20; |

&#x20; +---- INSUFFICIENT

&#x20;         |

&#x20;         v

&#x20;  Learned Halting Policy

&#x20;         |

&#x20;      +--+--+

&#x20;      |     |

&#x20;     STOP  CONTINUE

&#x20;             |

&#x20;             v

&#x20;       Query Rewriter

&#x20;             |

&#x20;             v

&#x20;         Retrieval

&#x20;             |

&#x20;             v

&#x20;          Critic

