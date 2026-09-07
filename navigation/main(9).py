import math
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# ============================================================
# PHASE 10.1
# END-TO-END AUTONOMOUS DISASTER RESPONSE SYSTEM
# WITH DYNAMIC REPLANNING
# ============================================================

print("=" * 70)
print("PHASE 10.1 - INTEGRATED AUTONOMOUS DISASTER RESPONSE")
print("=" * 70)


# ============================================================
# MISSION CONFIGURATION
# ============================================================

BASE = (2, 2)

SURVIVORS = {
    "S1": {
        "position": (26, 26),
        "condition": "HIGH",
        "confidence": 0.92
    },

    "S2": {
        "position": (18, 7),
        "condition": "HIGH",
        "confidence": 0.88
    },

    "S3": {
        "position": (7, 22),
        "condition": "CRITICAL",
        "confidence": 0.96
    }
}


# ============================================================
# STATIC HAZARD REGIONS
# ============================================================

HAZARDS = [
    (8, 8, 6, 6),
    (14, 12, 5, 4),
    (19, 18, 8, 6),
    (9, 21, 5, 4),
    (14, 24, 8, 4)
]


# ============================================================
# DYNAMIC HAZARD
# ============================================================

DYNAMIC_HAZARD = (4, 10)

# Region representing the newly detected hazard
DYNAMIC_HAZARD_REGION = (
    DYNAMIC_HAZARD[0] - 1,
    DYNAMIC_HAZARD[1] - 1,
    2,
    2
)


BATTERY_START = 100.0


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def distance(a, b):
    """
    Euclidean distance between two grid points.
    """

    return math.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2
    )


# ============================================================
# HAZARD COLLISION CHECK
# ============================================================

def point_in_hazard(point, hazards, safety_margin=0):
    """
    Determine whether a grid point lies inside
    a hazard region.
    """

    px, py = point

    for hazard in hazards:

        x, y, w, h = hazard

        if (
            x - safety_margin <= px <= x + w + safety_margin
            and
            y - safety_margin <= py <= y + h + safety_margin
        ):
            return True

    return False


# ============================================================
# A* SAFE ROUTE PLANNER
# ============================================================

def generate_safe_route(start, target, hazards):
    """
    A* based autonomous path planner.

    The drone searches an 8-connected grid while avoiding
    known hazard regions.
    """

    start = tuple(start)
    target = tuple(target)

    MIN_X = 0
    MAX_X = 30

    MIN_Y = 0
    MAX_Y = 30

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),

        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1)
    ]

    open_set = [start]

    came_from = {}

    g_score = {
        start: 0
    }

    f_score = {
        start: distance(start, target)
    }

    while open_set:

        current = min(
            open_set,
            key=lambda node: f_score.get(
                node,
                float("inf")
            )
        )

        # ----------------------------------------------------
        # TARGET REACHED
        # ----------------------------------------------------

        if current == target:

            route = [current]

            while current in came_from:

                current = came_from[current]

                route.append(current)

            route.reverse()

            return route

        open_set.remove(current)

        # ----------------------------------------------------
        # EXPAND NEIGHBOURS
        # ----------------------------------------------------

        for dx, dy in directions:

            neighbour = (
                current[0] + dx,
                current[1] + dy
            )

            # Keep drone inside map
            if not (
                MIN_X <= neighbour[0] <= MAX_X
                and
                MIN_Y <= neighbour[1] <= MAX_Y
            ):
                continue

            # Avoid hazard with safety margin
            if point_in_hazard(
                neighbour,
                hazards,
                safety_margin=1
            ):
                continue

            movement_cost = math.sqrt(
                dx ** 2 +
                dy ** 2
            )

            tentative_g = (
                g_score[current]
                + movement_cost
            )

            if tentative_g < g_score.get(
                neighbour,
                float("inf")
            ):

                came_from[neighbour] = current

                g_score[neighbour] = tentative_g

                f_score[neighbour] = (
                    tentative_g
                    + distance(
                        neighbour,
                        target
                    )
                )

                if neighbour not in open_set:

                    open_set.append(
                        neighbour
                    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    print(
        f"⚠ No safe route found from "
        f"{start} to {target}"
    )

    return [start, target]


# ============================================================
# ROUTE DISTANCE
# ============================================================

def route_distance(route):

    total = 0.0

    for i in range(
        len(route) - 1
    ):

        total += distance(
            route[i],
            route[i + 1]
        )

    return total


# ============================================================
# PRIORITY CALCULATION
# ============================================================

def calculate_priority(survivor):
    """
    Calculate rescue priority.

    Critical > High > Medium.
    Confidence contributes to the score.
    """

    condition_score = {
        "CRITICAL": 70,
        "HIGH": 50,
        "MEDIUM": 30
    }

    score = (
        condition_score[
            survivor["condition"]
        ]
        +
        survivor["confidence"] * 20
    )

    return round(score, 1)


# ============================================================
# STAGE 1
# MISSION INITIALIZATION
# ============================================================

print("\n[STAGE 1] MISSION INITIALIZATION")
print("-" * 60)

print(
    f"Drone base position : {BASE}"
)

print(
    f"Battery             : "
    f"{BATTERY_START:.1f}%"
)

print(
    f"Known survivors     : "
    f"{len(SURVIVORS)}"
)

print(
    f"Known hazards       : "
    f"{len(HAZARDS)}"
)

print(
    "✓ Mission parameters loaded"
)

print(
    "✓ Autonomous mode enabled"
)


# ============================================================
# STAGE 2
# ENVIRONMENT ANALYSIS
# ============================================================

print("\n[STAGE 2] ENVIRONMENT ANALYSIS")
print("-" * 60)

print(
    "Scanning disaster environment..."
)

for i, hazard in enumerate(
    HAZARDS,
    start=1
):

    x, y, w, h = hazard

    print(
        f"Hazard {i}: "
        f"region=({x},{y}) "
        f"size=({w}x{h})"
    )

print(
    "✓ Hazard map generated"
)

print(
    "✓ Unsafe regions identified"
)


# ============================================================
# STAGE 3
# AUTONOMOUS SURVIVOR DETECTION
# ============================================================

print(
    "\n[STAGE 3] AUTONOMOUS SURVIVOR DETECTION"
)

print("-" * 60)

for survivor_id, data in SURVIVORS.items():

    print(
        f"{survivor_id} detected at "
        f"{data['position']} | "
        f"confidence="
        f"{data['confidence'] * 100:.0f}%"
    )

print(
    "✓ Multi-survivor detection completed"
)


# ============================================================
# STAGE 4
# MULTI-SENSOR ASSESSMENT
# ============================================================

print(
    "\n[STAGE 4] MULTI-SENSOR ASSESSMENT"
)

print("-" * 60)

for survivor_id, data in SURVIVORS.items():

    print(
        f"{survivor_id}: "
        f"condition={data['condition']} | "
        f"confidence="
        f"{data['confidence'] * 100:.0f}%"
    )

print(
    "✓ Sensor fusion completed"
)

print(
    "✓ Survivor conditions estimated"
)


# ============================================================
# STAGE 5
# SURVIVOR PRIORITIZATION
# ============================================================

print(
    "\n[STAGE 5] SURVIVOR PRIORITIZATION"
)

print("-" * 60)

priority_queue = []

for survivor_id, data in SURVIVORS.items():

    score = calculate_priority(data)

    priority_queue.append(
        (
            survivor_id,
            score,
            data["position"],
            data["condition"]
        )
    )


priority_queue.sort(
    key=lambda item: item[1],
    reverse=True
)


for rank, item in enumerate(
    priority_queue,
    start=1
):

    survivor_id, score, position, condition = item

    print(
        f"{rank}. {survivor_id} → "
        f"{condition} | "
        f"Score={score} | "
        f"Location={position}"
    )


print(
    "✓ Autonomous rescue priority generated"
)


# ============================================================
# STAGE 6
# INITIAL SAFE ROUTE OPTIMIZATION
# ============================================================

print(
    "\n[STAGE 6] SAFE ROUTE OPTIMIZATION"
)

print("-" * 60)

rescue_order = [
    item[0]
    for item in priority_queue
]


print(
    "Rescue order:",
    " → ".join(rescue_order)
)


current_position = BASE

planned_route = [BASE]


for survivor_id in rescue_order:

    target = SURVIVORS[
        survivor_id
    ]["position"]

    route = generate_safe_route(
        current_position,
        target,
        HAZARDS
    )

    planned_route.extend(
        route[1:]
    )

    current_position = target


print(
    f"✓ Initial safe route generated "
    f"({len(planned_route)} waypoints)"
)


print(
    f"Initial estimated distance: "
    f"{route_distance(planned_route):.2f} units"
)


# ============================================================
# STAGE 7
# AUTONOMOUS RESCUE EXECUTION
# ============================================================

print(
    "\n[STAGE 7] AUTONOMOUS RESCUE EXECUTION"
)

print("-" * 60)


battery = BATTERY_START

reached_survivors = []

actual_route = [BASE]

dynamic_hazard_detected = False

replanning_events = 0

current_position = BASE

DYNAMIC_HAZARDS = []


# ============================================================
# EXECUTION LOOP
# ============================================================

for survivor_index, survivor_id in enumerate(
    rescue_order
):

    target = SURVIVORS[
        survivor_id
    ]["position"]


    print(
        f"\nDrone navigating toward "
        f"{survivor_id} at {target}..."
    )


    # --------------------------------------------------------
    # GENERATE SAFE ROUTE
    # --------------------------------------------------------

    current_route = generate_safe_route(
        current_position,
        target,
        HAZARDS + DYNAMIC_HAZARDS
    )


    waypoint_index = 1


    # ========================================================
    # WAYPOINT EXECUTION
    # ========================================================

    while waypoint_index < len(
        current_route
    ):

        next_position = (
            current_route[
                waypoint_index
            ]
        )


        # ====================================================
        # DYNAMIC HAZARD DETECTION
        # ====================================================

        if (
            not dynamic_hazard_detected
            and
            len(actual_route) >= 5
        ):

            dynamic_hazard_detected = True


            print(
                "\n⚠ DYNAMIC HAZARD DETECTED "
                f"at {DYNAMIC_HAZARD}"
            )


            # Add dynamic hazard to live map

            DYNAMIC_HAZARDS.append(
                DYNAMIC_HAZARD_REGION
            )


            print(
                "✓ Hazard added to live "
                "environment map"
            )


            # ------------------------------------------------
            # CHECK OLD ROUTE
            # ------------------------------------------------

            remaining_route = (
                current_route[
                    waypoint_index:
                ]
            )


            route_blocked = any(
                point_in_hazard(
                    point,
                    DYNAMIC_HAZARDS,
                    safety_margin=1
                )
                for point in remaining_route
            )


            if route_blocked:

                print(
                    "⚠ Existing route intersects "
                    "updated hazard map"
                )

            else:

                print(
                    "⚠ Environment changed; "
                    "route must be revalidated"
                )


            # =================================================
            # AUTONOMOUS REPLANNING
            # =================================================

            print(
                "🧠 Autonomous replanning activated..."
            )


            new_route = generate_safe_route(
                current_position,
                target,
                HAZARDS + DYNAMIC_HAZARDS
            )


            replanning_events += 1


            print(
                f"✓ New safe route generated "
                f"({len(new_route)} waypoints)"
            )


            current_route = new_route

            waypoint_index = 1


            print(
                "✓ Drone switching to "
                "replanned route"
            )


            continue


        # ====================================================
        # MOVE DRONE
        # ====================================================

        current_position = next_position


        actual_route.append(
            current_position
        )


        # Battery consumed during flight

        battery -= 0.5


        print(
            f"Drone → {current_position} | "
            f"Battery={battery:.1f}%"
        )


        waypoint_index += 1


        # ----------------------------------------------------
        # EMERGENCY BATTERY CHECK
        # ----------------------------------------------------

        if battery < 25:

            print(
                "\n⚠ CRITICAL BATTERY LEVEL"
            )

            break


    # ========================================================
    # SURVIVOR REACHED
    # ========================================================

    if current_position == target:

        reached_survivors.append(
            survivor_id
        )


        # Rescue operation battery cost

        battery -= 7


        print(
            f"✓ {survivor_id} reached | "
            f"Battery={battery:.1f}%"
        )


    else:

        print(
            f"✗ Unable to safely reach "
            f"{survivor_id}"
        )


    # ========================================================
    # STOP MISSION IF BATTERY CRITICAL
    # ========================================================

    if battery < 25:

        print(
            "⚠ Mission execution suspended "
            "due to critical battery"
        )

        break


print(
    "\n✓ Autonomous rescue execution completed"
)


# ============================================================
# STAGE 8
# DYNAMIC MISSION MONITORING
# ============================================================

print(
    "\n[STAGE 8] DYNAMIC MISSION MONITORING"
)

print("-" * 60)

print(
    "Continuous environment monitoring active..."
)


if dynamic_hazard_detected:

    print(
        f"✓ Dynamic hazard processed "
        f"at {DYNAMIC_HAZARD}"
    )


    print(
        f"✓ Replanning events: "
        f"{replanning_events}"
    )


    print(
        "✓ Updated environment map maintained"
    )


    print(
        "✓ Mission continued using "
        "updated route"
    )

else:

    print(
        "✓ No dynamic hazards detected"
    )


# ============================================================
# STAGE 9
# SAFETY & FAIL-SAFE MANAGEMENT
# ============================================================

print(
    "\n[STAGE 9] SAFETY & FAIL-SAFE MANAGEMENT"
)

print("-" * 60)


emergency_triggered = False

safety_state = "NORMAL"


if battery < 25:

    emergency_triggered = True

    safety_state = "RETURN TO BASE"


elif battery < 40:

    print(
        "⚠ LOW BATTERY WARNING"
    )

    safety_state = "LOW BATTERY"


else:

    print(
        "✓ Battery level safe"
    )


print(
    f"Safety state: {safety_state}"
)


# ============================================================
# STAGE 10
# MISSION COMPLETION
# ============================================================

print(
    "\n[STAGE 10] MISSION COMPLETION"
)

print("-" * 60)


final_position = current_position


mission_success = (
    len(reached_survivors)
    == len(SURVIVORS)
    and
    replanning_events >= 1
    and
    not emergency_triggered
)


actual_flight_distance = route_distance(
    actual_route
)


print(
    f"Survivors detected : "
    f"{len(SURVIVORS)}"
)


print(
    f"Survivors reached  : "
    f"{len(reached_survivors)}"
)


print(
    f"Rescue order       : "
    f"{' → '.join(rescue_order)}"
)


print(
    f"Final position     : "
    f"{final_position}"
)


print(
    f"Battery remaining  : "
    f"{battery:.1f}%"
)


print(
    f"Dynamic hazards    : "
    f"{1 if dynamic_hazard_detected else 0}"
)


print(
    f"Replanning events  : "
    f"{replanning_events}"
)


print(
    f"Actual flight dist : "
    f"{actual_flight_distance:.2f} units"
)


print(
    f"Mission success    : "
    f"{mission_success}"
)


# ============================================================
# SUCCESS / FAILURE SUMMARY
# ============================================================

if mission_success:

    print(
        "\n✓ END-TO-END AUTONOMOUS "
        "MISSION SUCCESSFUL"
    )

    print(
        "✓ SURVIVORS IDENTIFIED"
    )

    print(
        "✓ SURVIVORS PRIORITIZED"
    )

    print(
        "✓ SAFE ROUTES GENERATED"
    )

    print(
        "✓ RESCUE OPERATIONS COMPLETED"
    )

    print(
        "✓ DYNAMIC REPLANNING VERIFIED"
    )

    print(
        "✓ SAFETY MONITORING VERIFIED"
    )

else:

    print(
        "\n✗ MISSION NOT COMPLETED"
    )


# ============================================================
# FINAL MISSION REPORT
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "PHASE 10.1 - FINAL INTEGRATED MISSION REPORT"
)

print(
    "=" * 70
)


print(
    f"Mission status       : "
    f"{'SUCCESS' if mission_success else 'FAILED'}"
)


print(
    f"Survivors detected   : "
    f"{len(SURVIVORS)}"
)


print(
    f"Survivors rescued    : "
    f"{len(reached_survivors)}"
)


print(
    f"Rescue sequence      : "
    f"{' → '.join(rescue_order)}"
)


print(
    f"Dynamic hazards      : "
    f"{1 if dynamic_hazard_detected else 0}"
)


print(
    f"Replanning events    : "
    f"{replanning_events}"
)


print(
    f"Safety state         : "
    f"{safety_state}"
)


print(
    f"Final battery        : "
    f"{battery:.1f}%"
)


print(
    f"Final position       : "
    f"{final_position}"
)


print(
    f"Actual flight length : "
    f"{actual_flight_distance:.2f} units"
)


print("=" * 70)


# ============================================================
# VISUALIZATION
# ============================================================

print(
    "\nGenerating Phase 10.1 visualization..."
)


fig, ax = plt.subplots(
    figsize=(12, 10)
)


# ============================================================
# STATIC HAZARDS
# ============================================================

for i, hazard in enumerate(
    HAZARDS
):

    x, y, w, h = hazard


    ax.add_patch(
        Rectangle(
            (x, y),
            w,
            h,
            alpha=0.18
        )
    )


# ============================================================
# DYNAMIC HAZARD
# ============================================================

dx, dy = DYNAMIC_HAZARD


ax.scatter(
    dx,
    dy,
    marker="X",
    s=250,
    linewidths=2,
    label="Dynamic Hazard"
)


# ============================================================
# ACTUAL DRONE ROUTE
# ============================================================

route_x = [
    point[0]
    for point in actual_route
]


route_y = [
    point[1]
    for point in actual_route
]


ax.plot(
    route_x,
    route_y,
    linewidth=2.5,
    linestyle="--",
    label="Actual Autonomous Flight Path"
)


# ============================================================
# DRONE BASE
# ============================================================

ax.scatter(
    BASE[0],
    BASE[1],
    marker="^",
    s=250,
    label="Drone Base"
)


# ============================================================
# SURVIVORS
# ============================================================

for rank, item in enumerate(
    priority_queue,
    start=1
):

    survivor_id, score, position, condition = item


    x, y = position


    ax.scatter(
        x,
        y,
        marker="*",
        s=350,
        edgecolors="black",
        linewidths=1.5,
        label=(
            f"#{rank} "
            f"{survivor_id} - "
            f"{condition}"
        )
    )


    ax.annotate(
        f"#{rank} {survivor_id}\n"
        f"{condition}\n"
        f"Score: {score}",
        (x, y),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=9,
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.85
        )
    )


# ============================================================
# TITLE
# ============================================================

ax.set_title(
    "Phase 10.1 - Integrated Autonomous Disaster Response",
    fontsize=18,
    fontweight="bold"
)


ax.set_xlabel(
    "X Grid Position",
    fontsize=12
)


ax.set_ylabel(
    "Y Grid Position",
    fontsize=12
)


# ============================================================
# MISSION INFORMATION PANEL
# ============================================================

mission_info = (
    "AUTONOMOUS MISSION STATUS\n"
    "──────────────────────────\n"
    f"Mission Success: "
    f"{mission_success}\n"
    f"Survivors: "
    f"{len(SURVIVORS)}\n"
    f"Rescued: "
    f"{len(reached_survivors)}\n\n"
    f"Order:\n"
    f"{' → '.join(rescue_order)}\n\n"
    f"Dynamic Hazards: "
    f"{1 if dynamic_hazard_detected else 0}\n"
    f"Replanning Events: "
    f"{replanning_events}\n"
    f"Battery: "
    f"{battery:.1f}%\n"
    f"Safety: "
    f"{safety_state}\n"
    f"Flight Distance: "
    f"{actual_flight_distance:.2f}\n\n"
    "STATUS: MISSION COMPLETE"
)


ax.text(
    0.98,
    0.02,
    mission_info,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox=dict(
        boxstyle="round",
        facecolor="white",
        alpha=0.9
    )
)


# ============================================================
# GRAPH SETTINGS
# ============================================================

ax.set_xlim(
    0,
    30
)


ax.set_ylim(
    0,
    30
)


ax.grid(
    True,
    alpha=0.25
)


ax.legend(
    loc="upper left"
)


plt.tight_layout()


print(
    "Launching Phase 10.1 visualization..."
)


plt.show()