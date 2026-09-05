package com.bitcoinanalysis.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.math.BigDecimal;
import java.util.List;

@Entity
@Table(name = "transactions")
@Getter
@Setter
public class Transaction {

    @Id
    @Column(name = "txid")
    private String txid;

    @Column(name = "timestamp", nullable = false)
    private Long timestamp;

    @Column(name = "fee", precision = 20, scale = 8)
    private BigDecimal fee;

    @Column(name = "script_type")
    private String scriptType;

    @Column(name = "is_anomaly")
    private Boolean isAnomaly;

    @Column(name = "pattern_type")
    private String patternType;

    @OneToMany(mappedBy = "transaction", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TransactionInput> inputs;

    @OneToMany(mappedBy = "transaction", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TransactionOutput> outputs;

    @OneToMany(mappedBy = "transaction", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<NetworkMetadata> networkMetadata;

    @OneToMany(mappedBy = "transaction", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<AnalysisResult> analysisResults;
}