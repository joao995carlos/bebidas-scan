package br.com.bebidasscan.api;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(BebidasScanProperties.class)
public class BebidasScanApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(BebidasScanApiApplication.class, args);
    }
}
