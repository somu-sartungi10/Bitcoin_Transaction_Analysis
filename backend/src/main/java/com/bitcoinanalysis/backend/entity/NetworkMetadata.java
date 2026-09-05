package com.bitcoinanalysis.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "network_metadata")
@Getter
@Setter
public class NetworkMetadata {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "txid", nullable = false)
    private Transaction transaction;

    @Column(name = "src_ip")
    private String srcIp;   // stored as INET in DB, mapped as String in Java — simplest, avoids custom type converters

    @Column(name = "src_port")
    private Integer srcPort;

    @Column(name = "dst_ip")
    private String dstIp;

    @Column(name = "dst_port")
    private Integer dstPort;

    @Column(name = "geo_country")
    private String geoCountry;

    @Column(name = "asn")
    private String asn;
}