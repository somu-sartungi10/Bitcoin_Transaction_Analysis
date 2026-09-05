package com.bitcoinanalysis.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.math.BigDecimal;

@Entity
@Table(name = "transaction_inputs")
@Getter
@Setter
public class TransactionInput {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "txid", nullable = false)
    private Transaction transaction;

    @Column(name = "address")
    private String address;

    @Column(name = "amount", precision = 20, scale = 8)
    private BigDecimal amount;
}