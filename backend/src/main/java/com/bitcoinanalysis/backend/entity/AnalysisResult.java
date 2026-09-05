package com.bitcoinanalysis.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "analysis_results")
@Getter
@Setter
public class AnalysisResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "txid", nullable = false)
    private Transaction transaction;

    @Column(name = "risk_score", precision = 5, scale = 2)
    private BigDecimal riskScore;

    @Column(name = "risk_level")
    private String riskLevel;

    @Column(name = "predicted_pattern")
    private String predictedPattern;

    @Column(name = "confidence", precision = 4, scale = 3)
    private BigDecimal confidence;

    @Column(name = "model_version")
    private String modelVersion;

    @Column(name = "analyzed_at")
    private LocalDateTime analyzedAt;
}