package com.sde.audit.repo;

import com.sde.audit.model.Decision;
import com.sde.audit.model.DecisionStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DecisionRepository extends JpaRepository<Decision, Long> {

    List<Decision> findAllByOrderByCreatedAtDesc();

    List<Decision> findByStatusOrderByCreatedAtDesc(DecisionStatus status);

    long countByStatus(DecisionStatus status);

    long countByCustomerIdAndRecommendedActionAndStatus(
            String customerId, String recommendedAction, DecisionStatus status);

    List<Decision> findByCustomerIdAndStatusOrderByCreatedAtDesc(
            String customerId, DecisionStatus status);
}
